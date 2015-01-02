import json
import random
from weppy import request, session
from weppy.dal import Field, Model, before_insert, modelmethod, fieldmethod
from weppy.validators import inDB, isntEmpty, inSet, isIntInRage


class Game(Model):
    tablename = "games"

    fields = [
        Field("owner", "reference auth_user"),
        Field("map", "reference maps"),
        Field("name"),
        Field("nplayers", "integer"),
        Field("bet", "integer", default=10),
        Field("pottype", default="wta"),
        Field("phasetime", "integer", default=60*24),
        Field("jointime", "integer", default=60*24),
        Field("starton", default="asap"),
        Field("buildew", "boolean", default=False),
        Field("buildonstart", "boolean", default=False),
        Field("anonymous", "boolean", default=False),
        Field("presstype", default="all"),
        Field("countriesassign", default="random"),
        Field("countriesenabled", "json"),
        Field("access", default="free"),
        Field("maxturns", "integer", default=0),
        Field("targetsc", "integer", default=0),
        #Field("skipprocess", "json"),
        Field("status", default="pregame"),
        Field("active", "boolean", default=False),
        Field("ready", "boolean", default=False),
        Field("created", "datetime", default=lambda: request.now),
        Field("processed", "datetime", default=lambda: request.now),
        Field("next", "datetime"),
        Field("countries", "json"),
        Field("phases", "json")
    ]

    validators = {
        "name": isntEmpty(),
        "pottype": inSet(["wta", "ppsc"], zero=None),
        "phasetime": isIntInRage(5, 60*24*10),
        "jointime": isIntInRage(5, 60*24*10),
        "starton": inSet(["asap", "ontime"], zero=None),
        "presstype": inSet(["all", "globals", "none"], zero=None),
        "countriesassign": inSet(["random", "choose"], zero=None),
        "access": inSet(["free", "password"], zero=None)
    }

    visibility = {
        "owner": (False, False),
        "status": (False, False),
        "active": (False, False),
        "created": (False, False),
        "processed": (False, False),
        "next": (False, False),
        "ready": (False, False),
        #"countries": (False, False),
        "phases": (False, False),
        # temp disabled
        "targetsc": (False, False)
    }

    def set_validators(self):
        self.entity.map.requires = inDB(self.db, self.db.maps.id, zero=None)

    @fieldmethod('playercountry')
    def get_country(self, row):
        uid = session.auth.user.id if session.auth else None
        if not uid:
            return None
        from nudiplomacy.helpers.mongo import objidToLong
        for k, v in row.games.countries.items():
            if objidToLong(v) == uid:
                return k
        return None

    @before_insert
    def setup_game(self, fields):
        # build countries based on selected preferences
        ce = json.loads(fields['countriesenabled'])
        random.shuffle(ce)
        countrylist = ce[:fields['nplayers']]
        fields['countries'] = {}
        for name in countrylist:
            fields['countries'][name] = None
        if fields['countriesassign'] == "random":
            from nudiplomacy.helpers.mongo import longToObjid
            chosen = countrylist[0]
            fields['countries'][chosen] = longToObjid(session.auth.user.id)
        # init phases
        fields['phases'] = [{"type": "pre-game"}]


class Orders(Model):
    tablename = "orders"

    fields = [
        Field("player", "reference auth_user"),
        Field("game", "reference games"),
        Field("data", "json"),
        Field("ready", "boolean", default=False)
    ]

    @modelmethod
    def owned(db, entity, gid, owner=None):
        uid = owner or (session.auth.user.id if session.auth else None)
        if not uid:
            return {}
        rv = db((entity.game == gid) & (entity.player == uid)).select().first()
        if not rv:
            return {}
        return rv.data
