from weppy import tag


def games_map(field, value):
    db = field._db
    maps = db(db.Map.id > 0).select(db.Map.id, db.Map.name).as_list()
    choices = []
    for el in maps:
        choices.append(tag.option(el['name'], _value=el['id']))
    return tag.select(*choices, _id="games_map", _name="map",
                      _class="form-control")
