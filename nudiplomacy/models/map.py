from weppy.dal import Field, Model, before_insert, before_update, after_insert
from nudiplomacy import queue
from nudiplomacy.helpers.images import create_map_image


class Map(Model):
    tablename = "maps"

    fields = [
        Field("name"),
        Field("image", "upload"),
        Field("thumb", "upload"),
        Field("year", "integer"),
        Field("colors", "json"),
        Field("oxy", "json"),
        Field("neutrals", "json"),
        Field("seas", "json"),
        Field("coasts", "json"),
        Field("mcoasts", "json"),
        Field("same", "json"),
        Field("links", "json"),
        Field("supply", "json"),
        Field("homes", "json"),
        Field("names", "json"),
        Field("countries", "json"),
        Field("minplayers", "integer"),
        Field("scstowin", "integer"),
        Field("init", "json")
    ]

    visibility = {
        "thumb": (False, False)
    }

    # TODO: use queue for images
    @before_insert
    def create_thumb(self, fields):
        create_map_image(fields)

    @before_update
    def update_thumb(self, set, fields):
        self.create_thumb(fields)

    @after_insert
    def init_stats(self, fields, id):
        self.db.CountryStats.insert(map=id)
