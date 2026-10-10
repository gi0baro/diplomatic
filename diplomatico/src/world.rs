#[derive(Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Debug)]
pub(crate) struct Province(pub(crate) usize);

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub(crate) enum Fact {
    Kept,
    Taken(Province),
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub(crate) struct World(Vec<Fact>);

impl World {
    pub(crate) fn kept(provinces: usize) -> Self {
        Self(vec![Fact::Kept; provinces])
    }

    #[cfg(test)]
    pub(crate) fn len(&self) -> usize {
        self.0.len()
    }

    pub(crate) fn get(&self, province: Province) -> Fact {
        self.0[province.0]
    }

    pub(crate) fn set(&mut self, province: Province, fact: Fact) {
        self.0[province.0] = fact;
    }

    pub(crate) fn differences<'a>(&'a self, other: &'a World) -> impl Iterator<Item = Province> + 'a {
        (0..self.0.len())
            .map(Province)
            .filter(move |&p| self.get(p) != other.get(p))
    }
}

pub(crate) trait Rules {
    fn provinces(&self) -> usize;
    fn reads(&self, province: Province) -> Vec<Province>;
    fn candidates(&self, province: Province) -> Vec<Fact>;
    fn contest(&self, province: Province, world: &World) -> Fact;
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub(crate) struct Region {
    pub(crate) provinces: Vec<Province>,
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub(crate) enum Outcome {
    Unique,
    Degenerate(Vec<World>),
    Vacuum,
}
