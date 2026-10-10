use crate::world::{Fact, Outcome, Province, Region, Rules, World};

pub(crate) fn regions<R: Rules>(rules: &R) -> Vec<Region> {
    Tarjan::new(rules).run()
}

pub(crate) fn collapse<R: Rules>(rules: &R, region: &Region, world: &mut World) -> Outcome {
    let candidates: Vec<Vec<Fact>> = region.provinces.iter().map(|&p| rules.candidates(p)).collect();
    let mut stationary = Vec::new();
    let mut candidate = world.clone();
    let mut odometer = vec![0; candidates.len()];
    loop {
        for (i, &province) in region.provinces.iter().enumerate() {
            candidate.set(province, candidates[i][odometer[i]]);
        }
        if is_stationary(rules, region, &candidate) {
            stationary.push(candidate.clone());
        }
        if !advance(&mut odometer, &candidates) {
            break;
        }
    }
    match stationary.len() {
        1 => {
            *world = stationary.pop().unwrap();
            Outcome::Unique
        }
        0 => Outcome::Vacuum,
        _ => Outcome::Degenerate(stationary),
    }
}

fn is_stationary<R: Rules>(rules: &R, region: &Region, world: &World) -> bool {
    region.provinces.iter().all(|&p| rules.contest(p, world) == world.get(p))
}

fn advance(odometer: &mut [usize], candidates: &[Vec<Fact>]) -> bool {
    for (digit, options) in odometer.iter_mut().zip(candidates) {
        *digit += 1;
        if *digit < options.len() {
            return true;
        }
        *digit = 0;
    }
    false
}

struct Tarjan<'a, R: Rules> {
    rules: &'a R,
    index: Vec<Option<usize>>,
    lowlink: Vec<usize>,
    on_stack: Vec<bool>,
    stack: Vec<Province>,
    next_index: usize,
    regions: Vec<Region>,
}

impl<'a, R: Rules> Tarjan<'a, R> {
    fn new(rules: &'a R) -> Self {
        let n = rules.provinces();
        Self {
            rules,
            index: vec![None; n],
            lowlink: vec![0; n],
            on_stack: vec![false; n],
            stack: Vec::new(),
            next_index: 0,
            regions: Vec::new(),
        }
    }

    // Tarjan emits a component only after every component reachable from it,
    // so the output is already in collapse order: a region comes after all it reads.
    fn run(mut self) -> Vec<Region> {
        for i in 0..self.rules.provinces() {
            if self.index[i].is_none() {
                self.visit(Province(i));
            }
        }
        self.regions
    }

    fn visit(&mut self, province: Province) {
        let i = province.0;
        self.index[i] = Some(self.next_index);
        self.lowlink[i] = self.next_index;
        self.next_index += 1;
        self.stack.push(province);
        self.on_stack[i] = true;

        for read in self.rules.reads(province) {
            let j = read.0;
            match self.index[j] {
                None => {
                    self.visit(read);
                    self.lowlink[i] = self.lowlink[i].min(self.lowlink[j]);
                }
                Some(index) if self.on_stack[j] => {
                    self.lowlink[i] = self.lowlink[i].min(index);
                }
                Some(_) => {}
            }
        }

        if self.lowlink[i] == self.index[i].unwrap() {
            let mut provinces = Vec::new();
            loop {
                let member = self.stack.pop().unwrap();
                self.on_stack[member.0] = false;
                provinces.push(member);
                if member == province {
                    break;
                }
            }
            provinces.sort();
            self.regions.push(Region { provinces });
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct Toy {
        reads: Vec<Vec<usize>>,
        candidates: Vec<Vec<Fact>>,
        contest: fn(Province, &World) -> Fact,
    }

    impl Rules for Toy {
        fn provinces(&self) -> usize {
            self.reads.len()
        }

        fn reads(&self, province: Province) -> Vec<Province> {
            self.reads[province.0].iter().map(|&i| Province(i)).collect()
        }

        fn candidates(&self, province: Province) -> Vec<Fact> {
            self.candidates[province.0].clone()
        }

        fn contest(&self, province: Province, world: &World) -> Fact {
            (self.contest)(province, world)
        }
    }

    fn p(i: usize) -> Province {
        Province(i)
    }

    fn taken(i: usize) -> Fact {
        Fact::Taken(p(i))
    }

    fn ring_contest(province: Province, world: &World) -> Fact {
        let n = world.len();
        let next = p((province.0 + 1) % n);
        let prev = p((province.0 + n - 1) % n);
        if world.get(next) == Fact::Taken(province) { Fact::Taken(prev) } else { Fact::Kept }
    }

    fn ring(n: usize) -> Toy {
        Toy {
            reads: (0..n).map(|i| vec![(i + 1) % n]).collect(),
            candidates: (0..n).map(|i| vec![Fact::Kept, taken((i + n - 1) % n)]).collect(),
            contest: ring_contest,
        }
    }

    fn solve(rules: &impl Rules) -> (World, Vec<Outcome>) {
        let mut world = World::kept(rules.provinces());
        let outcomes = regions(rules).iter().map(|r| collapse(rules, r, &mut world)).collect();
        (world, outcomes)
    }

    #[test]
    fn a_pure_cycle_is_degenerate_between_all_moving_and_none_moving() {
        let (_, outcomes) = solve(&ring(3));
        assert_eq!(outcomes.len(), 1);
        let Outcome::Degenerate(worlds) = &outcomes[0] else { panic!("{outcomes:?}") };
        let mut all_kept = World::kept(3);
        let mut all_taken = World::kept(3);
        for i in 0..3 {
            all_taken.set(p(i), taken((i + 2) % 3));
            all_kept.set(p(i), Fact::Kept);
        }
        assert_eq!(worlds, &vec![all_kept, all_taken]);
    }

    #[test]
    fn a_chain_collapses_uniquely_from_its_end() {
        fn contest(province: Province, world: &World) -> Fact {
            match province.0 {
                2 => taken(1),
                1 => if world.get(p(2)) == taken(1) { taken(0) } else { Fact::Kept },
                _ => Fact::Kept,
            }
        }
        let toy = Toy {
            reads: vec![vec![1], vec![2], vec![]],
            candidates: vec![vec![Fact::Kept], vec![Fact::Kept, taken(0)], vec![Fact::Kept, taken(1)]],
            contest,
        };
        let expected_regions: Vec<Region> = [2, 1, 0].map(|i| Region { provinces: vec![p(i)] }).to_vec();
        assert_eq!(regions(&toy), expected_regions);

        let (world, outcomes) = solve(&toy);
        assert!(outcomes.iter().all(|o| *o == Outcome::Unique));
        assert_eq!(world.get(p(2)), taken(1));
        assert_eq!(world.get(p(1)), taken(0));
        assert_eq!(world.get(p(0)), Fact::Kept);
    }

    #[test]
    fn contradictory_rules_leave_a_vacuum() {
        fn contest(province: Province, world: &World) -> Fact {
            let other = p(1 - province.0);
            match (province.0, world.get(other)) {
                (0, Fact::Kept) => taken(1),
                (0, _) => Fact::Kept,
                (_, Fact::Kept) => Fact::Kept,
                _ => taken(0),
            }
        }
        let toy = Toy {
            reads: vec![vec![1], vec![0]],
            candidates: vec![vec![Fact::Kept, taken(1)], vec![Fact::Kept, taken(0)]],
            contest,
        };
        let (_, outcomes) = solve(&toy);
        assert_eq!(outcomes, vec![Outcome::Vacuum]);
    }

    #[test]
    fn regions_are_strongly_connected_components_in_collapse_order() {
        let toy = Toy {
            reads: vec![vec![1], vec![0, 2], vec![2], vec![]],
            candidates: vec![vec![Fact::Kept]; 4],
            contest: |_, _| Fact::Kept,
        };
        let found = regions(&toy);
        let cycle = Region { provinces: vec![p(0), p(1)] };
        let self_loop = Region { provinces: vec![p(2)] };
        let isolated = Region { provinces: vec![p(3)] };
        assert_eq!(found.len(), 3);
        assert!(found.iter().position(|r| *r == self_loop) < found.iter().position(|r| *r == cycle));
        assert!(found.contains(&isolated));
    }

    #[test]
    fn differences_lists_provinces_whose_fact_changed() {
        let mut a = World::kept(3);
        let b = World::kept(3);
        a.set(p(1), taken(0));
        assert_eq!(a.differences(&b).collect::<Vec<_>>(), vec![p(1)]);
    }
}
