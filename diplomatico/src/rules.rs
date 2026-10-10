use std::collections::BTreeSet;

use crate::orders::{Order as Input, OrderData};
use crate::world::{Fact, Province, Rules, World};

pub(crate) type Country = usize;

pub(crate) enum Via {
    Land,
    Bridge(Vec<Vec<Province>>),
}

pub(crate) enum Order {
    Hold,
    Move { to: Province, via: Via },
    SupportHold { target: Province },
    SupportMove { target: Province, to: Province },
    Convoy { army: Province },
}

pub(crate) struct Unit {
    pub(crate) country: Country,
    pub(crate) order: Order,
    pub(crate) failed: bool,
}

pub(crate) struct Turn {
    territories: Vec<u16>,
    units: Vec<Option<Unit>>,
    enters: Vec<Vec<Province>>,
    hold_supporters: Vec<Vec<Province>>,
    move_supporters: Vec<Vec<Province>>,
    crossings: Vec<Vec<Province>>,
    grounded: Vec<bool>,
}

impl Turn {
    pub(crate) fn new(inputs: &[Input]) -> Self {
        let territories = mentioned_territories(inputs);
        let province = |territory: u16| Province(territories.binary_search(&territory).unwrap());
        let mut countries: Vec<String> = Vec::new();
        let n = territories.len();
        let mut units: Vec<Option<Unit>> = (0..n).map(|_| None).collect();

        for input in inputs {
            let country = match countries.iter().position(|c| *c == input.country) {
                Some(i) => i,
                None => {
                    countries.push(input.country.clone());
                    countries.len() - 1
                }
            };
            let order = match (&input.data, input.failed) {
                (OrderData::Hold, _) => Order::Hold,
                (_, true) if !matches!(input.data, OrderData::Convoy(_)) => Order::Hold,
                (OrderData::Move(m), _) => Order::Move { to: province(m.dst), via: Via::Land },
                (OrderData::MoveViaConvoy(m), _) if m.routes.is_empty() => Order::Hold,
                (OrderData::MoveViaConvoy(m), _) => {
                    let routes = m.routes.iter().map(|r| r.iter().map(|&s| province(s)).collect()).collect();
                    Order::Move { to: province(m.dst), via: Via::Bridge(routes) }
                }
                (OrderData::SupportHold(s), _) => Order::SupportHold { target: province(s.dst) },
                (OrderData::SupportMove(s), _) => Order::SupportMove { target: province(s.src), to: province(s.dst) },
                (OrderData::Convoy(c), _) => Order::Convoy { army: province(c.src) },
            };
            units[province(input.territory).0] = Some(Unit { country, order, failed: input.failed });
        }

        let mut enters = vec![Vec::new(); n];
        let mut hold_supporters = vec![Vec::new(); n];
        let mut move_supporters = vec![Vec::new(); n];
        let mut crossings = vec![Vec::new(); n];
        for (i, unit) in units.iter().enumerate() {
            let here = Province(i);
            match unit.as_ref().map(|u| &u.order) {
                Some(Order::Move { to, via }) => {
                    enters[to.0].push(here);
                    if let Via::Bridge(routes) = via {
                        for sea in routes.iter().flatten().collect::<BTreeSet<_>>() {
                            crossings[sea.0].push(here);
                        }
                    }
                }
                Some(Order::SupportHold { target }) => hold_supporters[target.0].push(here),
                Some(Order::SupportMove { target, .. }) => move_supporters[target.0].push(here),
                _ => {}
            }
        }

        Self { territories, units, enters, hold_supporters, move_supporters, crossings, grounded: vec![false; n] }
    }

    pub(crate) fn territory(&self, province: Province) -> u16 {
        self.territories[province.0]
    }

    #[cfg(test)]
    pub(crate) fn province(&self, territory: u16) -> Option<Province> {
        self.territories.binary_search(&territory).ok().map(Province)
    }

    pub(crate) fn unit(&self, province: Province) -> Option<&Unit> {
        self.units[province.0].as_ref()
    }

    pub(crate) fn enters(&self, province: Province) -> &[Province] {
        &self.enters[province.0]
    }

    pub(crate) fn crossings(&self, sea: Province) -> &[Province] {
        &self.crossings[sea.0]
    }

    pub(crate) fn is_grounded(&self, army: Province) -> bool {
        self.grounded[army.0]
    }

    pub(crate) fn ground(&mut self, army: Province) {
        self.grounded[army.0] = true;
    }

    fn order(&self, province: Province) -> Option<&Order> {
        self.unit(province).map(|u| &u.order)
    }

    fn country(&self, province: Province) -> Option<Country> {
        self.unit(province).map(|u| u.country)
    }

    fn destination(&self, province: Province) -> Option<Province> {
        match self.order(province) {
            Some(Order::Move { to, .. }) => Some(*to),
            _ => None,
        }
    }

    fn moves_by_land(&self, province: Province, to: Province) -> bool {
        matches!(self.order(province), Some(Order::Move { to: t, via: Via::Land }) if *t == to)
    }

    fn head_to_head(&self, mover: Province, target: Province) -> bool {
        self.moves_by_land(mover, target) && self.moves_by_land(target, mover)
    }

    pub(crate) fn vacated(&self, province: Province, world: &World) -> bool {
        self.destination(province).is_some_and(|to| world.get(to) == Fact::Taken(province))
    }

    fn present(&self, mover: Province, world: &World) -> bool {
        match self.order(mover) {
            Some(Order::Move { via: Via::Land, .. }) => true,
            Some(Order::Move { via: Via::Bridge(routes), .. }) => {
                !self.is_grounded(mover) && routes.iter().any(|r| r.iter().all(|&sea| world.get(sea) == Fact::Kept))
            }
            _ => false,
        }
    }

    fn supported_against(&self, supporter: Province) -> Option<Province> {
        match self.order(supporter) {
            Some(Order::SupportMove { to, .. }) => Some(*to),
            _ => None,
        }
    }

    // A unit that supports an attack cannot have that support cut by the attacked unit
    // unless it is dislodged by it. Any other foreign unit that reaches the supporter cuts.
    pub(crate) fn cut(&self, supporter: Province, world: &World) -> bool {
        let country = self.country(supporter);
        self.enters[supporter.0].iter().any(|&attacker| {
            self.present(attacker, world)
                && self.country(attacker) != country
                && (self.supported_against(supporter) != Some(attacker) || world.get(supporter) == Fact::Taken(attacker))
        })
    }

    fn live_supports(&self, supporters: &[Province], world: &World, excluding: Option<Country>) -> u8 {
        supporters
            .iter()
            .filter(|&&s| excluding.is_none_or(|c| self.country(s) != Some(c)))
            .filter(|&&s| !self.cut(s, world))
            .count() as u8
    }

    fn holds_against(&self, province: Province, mover: Province, world: &World) -> bool {
        self.unit(province).is_some() && (self.head_to_head(mover, province) || !self.vacated(province, world))
    }

    fn stay_seen_by(&self, province: Province, mover: Province, world: &World) -> u8 {
        match self.order(province) {
            None => 0,
            Some(Order::Move { .. }) if self.head_to_head(mover, province) => {
                1 + self.live_supports(&self.move_supporters[province.0], world, None)
            }
            Some(Order::Move { .. }) if self.vacated(province, world) => 0,
            Some(Order::Move { .. }) => 1,
            Some(_) => 1 + self.live_supports(&self.hold_supporters[province.0], world, None),
        }
    }

    fn push(&self, mover: Province, target: Province, world: &World) -> u8 {
        let defender = self.holds_against(target, mover, world).then(|| self.country(target)).flatten();
        if defender.is_some() && defender == self.country(mover) {
            return 0;
        }
        1 + self.live_supports(&self.move_supporters[mover.0], world, defender)
    }

    fn prevent(&self, mover: Province, world: &World) -> u8 {
        let lost_head_to_head = self
            .destination(mover)
            .is_some_and(|to| self.head_to_head(mover, to) && world.get(mover) == Fact::Taken(to));
        if lost_head_to_head {
            return 0;
        }
        1 + self.live_supports(&self.move_supporters[mover.0], world, None)
    }

    fn cut_reads(&self, supporter: Province) -> Vec<Province> {
        let mut reads = Vec::new();
        for &attacker in &self.enters[supporter.0] {
            if let Some(Order::Move { via: Via::Bridge(routes), .. }) = self.order(attacker) {
                reads.extend(routes.iter().flatten());
            }
            if self.supported_against(supporter) == Some(attacker) {
                reads.push(supporter);
            }
        }
        reads
    }
}

impl Rules for Turn {
    fn provinces(&self) -> usize {
        self.territories.len()
    }

    fn reads(&self, province: Province) -> Vec<Province> {
        let mut reads = Vec::new();
        reads.extend(self.destination(province));
        for supporter in self.hold_supporters[province.0].iter().chain(&self.move_supporters[province.0]) {
            reads.extend(self.cut_reads(*supporter));
        }
        for &mover in &self.enters[province.0] {
            if let Some(Order::Move { via: Via::Bridge(routes), .. }) = self.order(mover) {
                reads.extend(routes.iter().flatten());
            }
            if self.head_to_head(mover, province) {
                reads.push(mover);
            }
            for &supporter in &self.move_supporters[mover.0] {
                reads.extend(self.cut_reads(supporter));
            }
        }
        reads.sort();
        reads.dedup();
        reads
    }

    fn candidates(&self, province: Province) -> Vec<Fact> {
        std::iter::once(Fact::Kept)
            .chain(self.enters[province.0].iter().map(|&m| Fact::Taken(m)))
            .collect()
    }

    fn contest(&self, province: Province, world: &World) -> Fact {
        let present: Vec<Province> =
            self.enters[province.0].iter().copied().filter(|&m| self.present(m, world)).collect();
        for &mover in &present {
            let push = self.push(mover, province, world);
            let beats_stay = push > self.stay_seen_by(province, mover, world);
            let beats_rivals = present.iter().filter(|&&c| c != mover).all(|&c| push > self.prevent(c, world));
            if beats_stay && beats_rivals {
                return Fact::Taken(mover);
            }
        }
        Fact::Kept
    }
}

fn mentioned_territories(inputs: &[Input]) -> Vec<u16> {
    let mut territories = BTreeSet::new();
    for input in inputs {
        territories.insert(input.territory);
        match &input.data {
            OrderData::Hold => {}
            OrderData::Move(m) => {
                territories.insert(m.dst);
            }
            OrderData::MoveViaConvoy(m) => {
                territories.insert(m.dst);
                territories.extend(m.routes.iter().flatten());
            }
            OrderData::SupportHold(s) => {
                territories.insert(s.dst);
            }
            OrderData::SupportMove(s) => {
                territories.insert(s.src);
                territories.insert(s.dst);
            }
            OrderData::Convoy(c) => {
                territories.insert(c.src);
                territories.insert(c.dst);
            }
        }
    }
    territories.into_iter().collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::collapse::{collapse, regions};
    use crate::orders::{Convoyed, Convoyer, Move, SupportMove};
    use crate::world::Outcome;

    fn order(territory: u16, country: &str, data: OrderData) -> Input {
        Input { territory, country: country.to_string(), data, failed: false }
    }

    fn mv(territory: u16, country: &str, dst: u16) -> Input {
        order(territory, country, OrderData::Move(Move { dst }))
    }

    fn via(territory: u16, country: &str, dst: u16, routes: Vec<Vec<u16>>) -> Input {
        order(territory, country, OrderData::MoveViaConvoy(Convoyed { dst, routes }))
    }

    fn sm(territory: u16, country: &str, src: u16, dst: u16) -> Input {
        order(territory, country, OrderData::SupportMove(SupportMove { src, dst }))
    }

    fn convoy(territory: u16, country: &str, src: u16, dst: u16) -> Input {
        order(territory, country, OrderData::Convoy(Convoyer { src, dst }))
    }

    fn solve(turn: &Turn) -> (World, Vec<Outcome>) {
        let mut world = World::kept(turn.provinces());
        let outcomes = regions(turn).iter().map(|r| collapse(turn, r, &mut world)).collect();
        (world, outcomes)
    }

    fn fact(turn: &Turn, world: &World, territory: u16) -> Fact {
        world.get(turn.province(territory).unwrap())
    }

    fn taken(turn: &Turn, territory: u16) -> Fact {
        Fact::Taken(turn.province(territory).unwrap())
    }

    const VENICE: u16 = 1;
    const TYROLIA: u16 = 2;
    const VIENNA: u16 = 3;

    #[test]
    fn simple_bounce() {
        let turn = Turn::new(&[mv(VENICE, "Italy", TYROLIA), mv(VIENNA, "Austria", TYROLIA)]);
        let (world, outcomes) = solve(&turn);
        assert!(outcomes.iter().all(|o| *o == Outcome::Unique));
        assert_eq!(fact(&turn, &world, TYROLIA), Fact::Kept);
    }

    const BERLIN: u16 = 10;
    const PRUSSIA: u16 = 11;
    const KIEL: u16 = 12;
    const SILESIA: u16 = 13;

    #[test]
    fn dislodged_unit_has_no_effect_on_attackers_area() {
        let turn = Turn::new(&[
            mv(BERLIN, "Germany", PRUSSIA),
            mv(KIEL, "Germany", BERLIN),
            sm(SILESIA, "Germany", BERLIN, PRUSSIA),
            mv(PRUSSIA, "Russia", BERLIN),
        ]);
        let head_to_head = regions(&turn)
            .into_iter()
            .find(|r| r.provinces.len() == 2)
            .expect("Berlin and Prussia read each other");
        assert_eq!(head_to_head.provinces, vec![turn.province(BERLIN).unwrap(), turn.province(PRUSSIA).unwrap()]);

        let (world, outcomes) = solve(&turn);
        assert!(outcomes.iter().all(|o| *o == Outcome::Unique));
        assert_eq!(fact(&turn, &world, PRUSSIA), taken(&turn, BERLIN));
        assert_eq!(fact(&turn, &world, BERLIN), taken(&turn, KIEL));
    }

    const LONDON: u16 = 20;
    const WALES: u16 = 21;
    const CHANNEL: u16 = 22;
    const BREST: u16 = 23;

    fn simple_convoy_paradox() -> Turn {
        Turn::new(&[
            sm(LONDON, "England", WALES, CHANNEL),
            mv(WALES, "England", CHANNEL),
            via(BREST, "France", LONDON, vec![vec![CHANNEL]]),
            convoy(CHANNEL, "France", BREST, LONDON),
        ])
    }

    #[test]
    fn simple_convoy_paradox_is_a_degeneracy_of_the_channel_alone() {
        let turn = simple_convoy_paradox();
        let channel = turn.province(CHANNEL).unwrap();
        let first = &regions(&turn)[0];
        assert_eq!(first.provinces, vec![channel]);

        let mut world = World::kept(turn.provinces());
        let Outcome::Degenerate(worlds) = collapse(&turn, first, &mut world) else { panic!() };
        assert_eq!(worlds.len(), 2);
        assert_eq!(worlds[0].differences(&worlds[1]).collect::<Vec<_>>(), vec![channel]);
        assert!(!turn.crossings(channel).is_empty());
    }

    #[test]
    fn simple_convoy_paradox_after_grounding_brest() {
        let mut turn = simple_convoy_paradox();
        turn.ground(turn.province(BREST).unwrap());
        let (world, outcomes) = solve(&turn);
        assert!(outcomes.iter().all(|o| *o == Outcome::Unique));
        assert_eq!(fact(&turn, &world, CHANNEL), taken(&turn, WALES));
        assert_eq!(fact(&turn, &world, LONDON), Fact::Kept);
    }
}
