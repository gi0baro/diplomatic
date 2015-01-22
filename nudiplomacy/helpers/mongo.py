# -*- coding: utf-8 -*-
from weppy import sdict


def longToObjid(arg):
    from bson.objectid import ObjectId
    if isinstance(arg, basestring):
        arg = long(arg)
    hexvalue = hex(arg)[2:].replace("L", "")
    return ObjectId(hexvalue)


def objidToLong(arg):
    from bson.objectid import ObjectId
    if isinstance(arg, ObjectId):
        return long(str(arg), 16)
    return arg


class MongoTable(object):
    def __init__(self, name, db):
        self.name = name
        self._db = db
        #self.find = partial(self._find, table=name)
        #self.upd = partial(self._update, table=name)
        self.find = self._find
        self.save = self._insert
        self.upd = self._update
        from functools import partial
        self.ioru = partial(self._update, upsert=True)
        self.fandm = self._findmodify

    @staticmethod
    def _map_query_id(query):
        if query.get("id"):
            newId = longToObjid(query["id"])
            query["_id"] = newId
            del query["id"]
        return query

    @staticmethod
    def _map_object(obj):
        if obj:
            obj["id"] = objidToLong(obj.get("_id", ""))
            obj = (sdict(obj))
        return obj

    def _insert(self, obj):
        _table = self._db[self.name]
        return _table.insert(obj)

    def _find(self, query=None, sort=None, limit=0, skip=0):
        table = self.name
        try:
            _table = self._db[table]
        except:
            return list()
        if sort:
            if not isinstance(sort, list):
                sort = [sort]
        query = MongoTable._map_query_id(query)
        objs = _table.find(spec=query, sort=sort, skip=skip, limit=limit)
        rows = []
        for obj in objs:
            rows.append(MongoTable._map_object(obj))
        return rows

    def _update(self, query=None, update=None, upsert=False):
        table = self.name
        _table = self._db[table]
        query = MongoTable._map_query_id(query)
        _table.update(query, update, upsert)

    def _findmodify(self, query=None, update=None, fields=None, upsert=False,
                    new=False):
        table = self.name
        try:
            _table = self._db[table]
        except:
            return None
        query = MongoTable._map_query_id(query)
        rv = _table.find_and_modify(query, update, upsert, new=new,
                                    fields=fields)
        return MongoTable._map_object(rv)


class MongoDB(object):
    def __init__(self, db):
        self._db = db._adapter.connection

    def __getattr__(self, name):
        if not hasattr(self, name):
            self.__setattr__(name, MongoTable(name, self._db))
        return object.__getattribute__(self, name)


#class MongoDB(object):
#    def __init__(self, db):
#        self.dal = db
#        self._db = self.dal._adapter.connection
#        self.db = MongoStorage(self._db)
