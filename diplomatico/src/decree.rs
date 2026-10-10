use std::collections::BTreeSet;

use anyhow::{anyhow, Result};

use crate::rules::Turn;
use crate::world::{Fact, Province, Region, World};

#[derive(Clone, PartialEq, Eq, Debug)]
pub(crate) enum Decree {
    BridgesFall(Vec<Province>),
    EveryoneRolls(World),
}

pub(crate) fn on_degeneracy(turn: &Turn, worlds: &[World]) -> Result<Decree> {
    let differing: BTreeSet<Province> = worlds[1..].iter().flat_map(|w| worlds[0].differences(w)).collect();
    let bridging = armies_crossing(turn, differing.iter().copied());
    if !bridging.is_empty() {
        return Ok(Decree::BridgesFall(bridging));
    }
    worlds
        .iter()
        .find(|w| differing.iter().all(|&p| w.get(p) != Fact::Kept))
        .map(|w| Decree::EveryoneRolls(w.clone()))
        .ok_or_else(|| anyhow!("degeneracy without a world in which every contested province is taken"))
}

pub(crate) fn on_vacuum(turn: &Turn, region: &Region) -> Result<Decree> {
    let contested = region.provinces.iter().copied().filter(|&p| !turn.enters(p).is_empty());
    let bridging = armies_crossing(turn, contested);
    if bridging.is_empty() {
        return Err(anyhow!("vacuum with no bridge to fell"));
    }
    Ok(Decree::BridgesFall(bridging))
}

fn armies_crossing(turn: &Turn, seas: impl Iterator<Item = Province>) -> Vec<Province> {
    seas.flat_map(|sea| turn.crossings(sea))
        .copied()
        .filter(|&army| !turn.is_grounded(army))
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect()
}
