import glob
import os

import click

from . import Map, StatsCountries, StatsGames, User, app, db
from .fixtures import load_scenario, play
from .variants import load


@app.command()
def load_maps():
    folder = os.path.join(app.root_path, "..", "variants")
    with db.connection():
        stored = {}
        for row in Map.all().select(Map.name, Map.revision):
            stored[row.name] = max(stored.get(row.name, 0), row.revision)
        for path in sorted(glob.glob(os.path.join(folder, "*", "*.yaml"))):
            variant = load(path)
            if stored.get(variant["name"], 0) >= variant["revision"]:
                continue
            res = Map.create(**variant)
            if res.errors:
                raise click.ClickException(f"{path}: {res.errors}")
            if not StatsCountries.get(variant=variant["name"]):
                zero = dict.fromkeys(variant["countries"], 0)
                StatsCountries.create(
                    variant=variant["name"], played=zero, won=zero, survived=zero, defeated=zero, drawn=zero
                )
                StatsGames.create(variant=variant["name"])
            print(f"Loaded {variant['name']} revision {variant['revision']}")
        db.commit()


@app.command()
def create_test_data():
    with db.connection():
        for idx in range(1, 11):
            key = f"tester{idx}"
            User.create(email="{}@diplomatic.com".format(key), password="foobar", username=key)
        db.commit()


@app.command()
@click.argument("scenario")
def fixture(scenario):
    folder = os.path.join(app.root_path, "..", "fixtures")
    path = scenario
    if os.sep not in scenario and not scenario.endswith((".yaml", ".yml")):
        path = os.path.join(folder, f"{scenario}.yaml")
    if not os.path.isfile(path):
        names = sorted(os.path.basename(name)[:-5] for name in glob.glob(os.path.join(folder, "*.yaml")))
        raise click.ClickException(f"{scenario}: no such scenario (in fixtures/: {', '.join(names) or 'none'})")
    scenario = load_scenario(path)
    with db.connection():
        play(scenario)
