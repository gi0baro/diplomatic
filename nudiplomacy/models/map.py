from weppy.dal import Field, Model


class Map(Model):
    tablename = "maps"

    fields = [
        Field("name"),
        Field("image", "upload"),
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
