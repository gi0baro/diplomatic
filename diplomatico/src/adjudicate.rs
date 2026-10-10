use anyhow::Result;

use crate::collapse::{collapse, regions};
use crate::decree::{on_degeneracy, on_vacuum, Decree};
use crate::orders::Order as Input;
use crate::rules::{Order, Turn};
use crate::world::{Fact, Outcome, Province, Rules, World};

#[derive(Clone, PartialEq, Eq, Debug)]
pub(crate) struct Verdict {
    pub(crate) territory: u16,
    pub(crate) succeeded: bool,
    pub(crate) dislodged: bool,
}

pub(crate) fn adjudicate(inputs: &[Input]) -> Result<Vec<Verdict>> {
    let mut turn = Turn::new(inputs);
    let world = resolve(&mut turn)?;
    Ok((0..turn.provinces())
        .map(Province)
        .filter_map(|p| turn.unit(p).map(|u| (p, u)))
        .map(|(p, unit)| {
            let dislodged = matches!(world.get(p), Fact::Taken(_)) && !turn.vacated(p, &world);
            let succeeded = !unit.failed
                && match unit.order {
                    Order::Hold => !dislodged,
                    Order::Move { to, .. } => world.get(to) == Fact::Taken(p),
                    Order::SupportHold { .. } | Order::SupportMove { .. } => !dislodged && !turn.cut(p, &world),
                    Order::Convoy { army } => !dislodged && !turn.is_grounded(army),
                };
            Verdict { territory: turn.territory(p), succeeded, dislodged }
        })
        .collect())
}

fn resolve(turn: &mut Turn) -> Result<World> {
    let mut world = World::kept(turn.provinces());
    for region in regions(turn) {
        loop {
            let decree = match collapse(turn, &region, &mut world) {
                Outcome::Unique => break,
                Outcome::Degenerate(worlds) => on_degeneracy(turn, &worlds)?,
                Outcome::Vacuum => on_vacuum(turn, &region)?,
            };
            match decree {
                Decree::BridgesFall(armies) => armies.into_iter().for_each(|a| turn.ground(a)),
                Decree::EveryoneRolls(chosen) => {
                    world = chosen;
                    break;
                }
            }
        }
    }
    Ok(world)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::orders::{Convoyed, Convoyer, Move, OrderData, SupportMove};

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

    fn failures(inputs: &[Input]) -> Vec<u16> {
        adjudicate(inputs).unwrap().into_iter().filter(|v| !v.succeeded).map(|v| v.territory).collect()
    }

    fn dislodged(inputs: &[Input]) -> Vec<u16> {
        adjudicate(inputs).unwrap().into_iter().filter(|v| v.dislodged).map(|v| v.territory).collect()
    }

    const LONDON: u16 = 1;
    const WALES: u16 = 2;
    const CHANNEL: u16 = 3;
    const BREST: u16 = 4;
    const BELGIUM: u16 = 5;
    const NORTH_SEA: u16 = 6;

    #[test]
    fn simple_convoy_paradox() {
        let inputs = [
            sm(LONDON, "England", WALES, CHANNEL),
            mv(WALES, "England", CHANNEL),
            via(BREST, "France", LONDON, vec![vec![CHANNEL]]),
            convoy(CHANNEL, "France", BREST, LONDON),
        ];
        assert_eq!(failures(&inputs), vec![CHANNEL, BREST]);
        assert_eq!(dislodged(&inputs), vec![CHANNEL]);
    }

    #[test]
    fn pandins_paradox_is_a_vacuum_resolved_by_felling_the_bridge() {
        let inputs = [
            sm(LONDON, "England", WALES, CHANNEL),
            mv(WALES, "England", CHANNEL),
            via(BREST, "France", LONDON, vec![vec![CHANNEL]]),
            convoy(CHANNEL, "France", BREST, LONDON),
            sm(NORTH_SEA, "Germany", BELGIUM, CHANNEL),
            mv(BELGIUM, "Germany", CHANNEL),
        ];
        assert_eq!(failures(&inputs), vec![WALES, CHANNEL, BREST, BELGIUM]);
        assert_eq!(dislodged(&inputs), Vec::<u16>::new());
    }

    const TRIESTE: u16 = 10;
    const SERBIA: u16 = 11;
    const BULGARIA: u16 = 12;
    const AEGEAN: u16 = 13;
    const IONIAN: u16 = 14;
    const ADRIATIC: u16 = 15;
    const NAPLES: u16 = 16;

    #[test]
    fn circular_movement_with_attacked_convoy_rolls() {
        let inputs = [
            mv(TRIESTE, "Austria", SERBIA),
            mv(SERBIA, "Austria", BULGARIA),
            via(BULGARIA, "Turkey", TRIESTE, vec![vec![AEGEAN, IONIAN, ADRIATIC]]),
            convoy(AEGEAN, "Turkey", BULGARIA, TRIESTE),
            convoy(IONIAN, "Turkey", BULGARIA, TRIESTE),
            convoy(ADRIATIC, "Turkey", BULGARIA, TRIESTE),
            mv(NAPLES, "Italy", IONIAN),
        ];
        assert_eq!(failures(&inputs), vec![NAPLES]);
    }
}
