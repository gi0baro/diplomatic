from weppy.dal import Field, Model, after_insert, after_update, modelmethod
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

    @after_insert
    def init_stats(self, fields, id):
        self.db.CountryStats.insert(map=id)

    @after_insert
    def create_thumb(self, fields, id):
        queue.save(create_map_image, 'misc', rid=id)

    @after_update
    def update_thumb(self, set, fields):
        if fields.get('image'):
            row = set.select().first()
            queue.save(create_map_image, 'misc', rid=row.id)

    @modelmethod
    def get_data(db, entity, mid=None, row=None):
        if row:
            mapdata = row.as_dict()
            del mapdata["image_blob"]
            del mapdata["thumb_blob"]
        else:
            fields = []
            for field in entity:
                if not field.name.endswith("blob"):
                    fields.append(field.name)
            sel = [entity[fname] for fname in fields]
            mapdata = db(entity.id == mid).select(*sel).first()
            if not mapdata:
                return dict()
            mapdata = mapdata.as_dict()
        ch = ["neutrals", "seas", "coasts"]
        for c in ch:
            for i in range(0, len(mapdata[c])):
                mapdata[c][i] = str(mapdata[c][i])
        return mapdata
