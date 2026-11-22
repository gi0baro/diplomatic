from emmett.orm import Field, has_many, scope

from . import TSModel


class Map(TSModel):
    has_many("games")

    name = Field(notnull=True)
    revision = Field.int(default=1)
    year = Field.int(notnull=True)
    min_players = Field.int(notnull=True)
    scs_to_win = Field.int(notnull=True)
    neutrals = Field.json()
    seas = Field.json()
    coasts = Field.json()
    multi_coasts = Field.json()
    coast_names = Field.json()
    links = Field.json()
    supply_centers = Field.json()
    home_centers = Field.json()
    names = Field.json()
    codes = Field.json()
    countries = Field.json()
    init = Field.json()
    svg = Field.text(auto_validation=False)

    validation = {"revision": {"gt": 0}, "min_players": {"gte": 2}, "scs_to_win": {"gt": 0}}

    default_values = {
        "neutrals": {},
        "seas": {},
        "coasts": {},
        "multi_coasts": [],
        "coast_names": {},
        "links": {"armies": [], "fleets": [], "multi_coasts": []},
        "supply_centers": [],
        "home_centers": {},
        "codes": {},
        "countries": {},
        "init": {"territories": {}, "troops": {}, "coasts": {}},
    }

    indexes = {"uniq_revision": {"fields": ["name", "revision"], "unique": True}}

    @scope("all_latest")
    def _all_latest(self):
        newest = (
            self.db(self.table)
            .nested_select(
                self.name,
                self.revision.max().with_alias("revision"),
                groupby=self.name,
            )
            .with_alias("newest")
        )
        return (self.name == newest.name) & (self.revision == newest.revision)

    @classmethod
    def target_centers_range(cls, row):
        #: the centres to win a game may ask for: more than any country starts with, at most all of them.
        #: Takes any row with `supply_centers` and `init`: a partial select has no row methods
        centers = set(row.supply_centers)
        most = max(len(centers & set(owned)) for owned in row.init["territories"].values())
        return most + 1, len(centers)
