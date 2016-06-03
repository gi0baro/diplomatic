from weppy.dal import Field, Model, after_insert, after_update
from nudiplomacy import queue
from nudiplomacy.helpers.images import create_map_image


class Map(Model):
    name = Field()
    image = Field('upload')
    thumb = Field('upload')
    year = Field('int')
    colors = Field('json')
    oxy = Field('json')
    neutrals = Field('json')
    seas = Field('json')
    coasts = Field('json')
    multi_coasts = Field('json')
    same = Field('json')
    links = Field('json')
    supply = Field('json')
    homes = Field('json')
    names = Field('json')
    countries = Field('json')
    min_players = Field('int')
    scs_towin = Field('int')
    init = Field('json')

    form_rw = {
        'thumb': False
    }

    @after_insert
    def init_stats(self, fields, rid):
        self.db.CountryStats.insert(map=rid)

    @after_insert
    def create_thumb(self, fields, rid):
        queue.save(create_map_image, 'misc', rid=rid)

    @after_update
    def update_thumb(self, dbset, fields):
        if fields.get('image'):
            row = dbset.select().first()
            queue.save(create_map_image, 'misc', rid=row.id)

    @classmethod
    def get_data(cls, mid=None, row=None):
        if row:
            mapdata = row.as_dict()
            #del mapdata["image_blob"]
            #del mapdata["thumb_blob"]
        else:
            fields = []
            for field in cls.table:
                if not field.name.endswith("blob"):
                    fields.append(field.name)
            sel = [cls.table[fname] for fname in fields]
            mapdata = cls.db(cls.id == mid).select(*sel).first()
            if not mapdata:
                return dict()
            mapdata = mapdata.as_dict()
        ch = ["neutrals", "seas", "coasts"]
        for c in ch:
            for i in range(0, len(mapdata[c])):
                mapdata[c][i] = str(mapdata[c][i])
        return mapdata
