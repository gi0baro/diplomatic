# -*- coding: utf-8 -*-

from emmett.orm import Field, has_many, scope

from . import TSModel


# from diplomatic import queue
# from diplomatic.helpers.images import create_map_image


class Map(TSModel):
    has_many("games")

    name = Field(notnull=True)
    revision = Field.int(default=1)
    year = Field.int(notnull=True)
    min_players = Field.int(notnull=True)
    scs_to_win = Field.int(notnull=True)
    colors = Field.json()
    oxy = Field.json()
    neutrals = Field.json()
    seas = Field.json()
    coasts = Field.json()
    multi_coasts = Field.json()
    same = Field.json()
    links = Field.json()
    supply_centers = Field.json()
    home_centers = Field.json()
    names = Field.json()
    countries = Field.json()
    init = Field.json()
    image = Field.upload()
    thumb = Field.upload()

    validation = {"revision": {"gt": 0}, "min_players": {"gte": 2}, "scs_to_win": {"gt": 0}}

    default_values = {
        "colors": {},
        "oxy": {},
        "neutrals": {},
        "seas": {},
        "coasts": {},
        "multi_coasts": {},
        "same": {},
        "links": {"armies": [], "fleets": [], "multi_coasts": []},
        "supply_centers": {},
        "home_centers": {},
        "countries": {},
        "init": {"territories": {}, "troops": {}, "coasts": {}},
    }

    fields_rw = {"thumb": False}
    indexes = {"uniq_revision": {"fields": ["name", "revision"], "unique": True}}

    @scope("all_latest")
    def _all_latest(self):
        newest = self.db(self.table).nested_select(
            self.name, self.revision.max().with_alias("revision"), groupby=self.name,
        ).with_alias("newest")
        return (self.name == newest.name) & (self.revision == newest.revision)

    # @after_insert
    # def init_stats(self, fields, rid):
    #     self.db.CountryStats.insert(map=rid)

    # @after_insert
    # def create_thumb(self, fields, rid):
    #     queue.save(create_map_image, 'misc', rid=rid)

    # @after_update
    # def update_thumb(self, dbset, fields):
    #     if fields.get('image'):
    #         row = dbset.select().first()
    #         queue.save(create_map_image, 'misc', rid=row.id)
