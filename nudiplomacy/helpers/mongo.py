# -*- coding: utf-8 -*-
import collections
from functools import partial
from weppy import sdict


def longToObjid(arg):
    from bson.objectid import ObjectId
    if isinstance(arg, str):
        arg = int(arg)
    hexvalue = hex(arg)[2:].replace("L", "")
    return ObjectId(hexvalue)


def objidToLong(arg):
    from bson.objectid import ObjectId
    if isinstance(arg, ObjectId):
        return int(str(arg), 16)
    return arg


class MongoTable(object):
    def __init__(self, name, db):
        self.name = name
        self._db = db
        self.find = self._find
        self.save = self._insert
        self.upd = self._update
        self.ioru = partial(self._update, upsert=True)
        self.fandm = self._findmodify
        self.rem = self._remove
        self.aggregate = self._aggregate
        self.count = self._count

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
            obj["id"] = obj.get('id', objidToLong(obj.get("_id", "")))
        return sdict(obj or {})

    def _insert(self, obj):
        _table = self._db[self.name]
        if isinstance(obj, collections.Iterable) and not isinstance(obj, dict):
            for el in obj:
                _table.insert_one(el)
            return
        if isinstance(obj, list):
            if not obj:
                return []
            return _table.insert_many(obj).inserted_ids
        return _table.insert_one(obj).inserted_id

    def _find(self, query={}, sort=None, limit=0, skip=0, map_id=True):
        table = self.name
        try:
            _table = self._db[table]
        except:
            return []
        if sort:
            if not isinstance(sort, list):
                sort = [sort]
        if map_id:
            query = MongoTable._map_query_id(query)
        objs = _table.find(query, sort=sort, skip=skip, limit=limit)
        rows = []
        for obj in objs:
            rows.append(MongoTable._map_object(obj))
        return rows

    def _count(self, query={}, map_id=True):
        table = self.name
        try:
            _table = self._db[table]
        except:
            return 0
        if map_id:
            query = MongoTable._map_query_id(query)
        return _table.count(query)

    def _update(self, query={}, update=None, upsert=False):
        table = self.name
        _table = self._db[table]
        query = MongoTable._map_query_id(query)
        _table.update(query, update, upsert)

    def _findmodify(self, query={}, update=None, fields=None, upsert=False,
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

    def _remove(self, *args, **kwargs):
        table = self.name
        _table = self._db[table]
        return _table.remove(*args, **kwargs)

    def _aggregate(self, *args, **kwargs):
        _table = self._db[self.name]
        objs = list(_table.aggregate(*args, **kwargs))
        rows = []
        for obj in objs:
            rows.append(sdict(obj))
        return rows


class MongoDB(object):
    def __init__(self, db):
        self._dal = db._adapter

    @property
    def _db(self):
        return self._dal.connection

    def __getattr__(self, name):
        setattr(self, name, MongoTable(name, self._db))
        return self[name]

    def __getitem__(self, name):
        return getattr(self, name)
