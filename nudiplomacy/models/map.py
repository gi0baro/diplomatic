from weppy.dal import Field, Model, after_insert, after_update
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
    #@before_insert
    #def create_thumb(self, fields):
    #    create_map_image(fields)

    #@before_update
    #def update_thumb(self, set, fields):
    #    self.create_thumb(fields)

    @after_insert
    def init_stats(self, fields, id):
        self.db.CountryStats.insert(map=id)

    @after_insert
    def create_thumb(self, fields, id):
        #queue.save(create_map_image, 'misc', fields=fields)
        queue.save(create_map_image, 'misc', rid=id)

    @after_update
    def update_thumb(self, set, fields):
        if fields.get('image'):
            row = set.select().first()
            queue.save(create_map_image, 'misc', rid=row.id)
