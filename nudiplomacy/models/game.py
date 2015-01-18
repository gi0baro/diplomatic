import json
import random
from weppy import request, session, T
from weppy.dal import Field, Model, before_insert, modelmethod, fieldmethod
from weppy.validators import inDb, isntEmpty, inSet, isIntInRange


_repr_pot = {'wta': T("Winner takes all"),
             'ppsc': T("Points per supply center")}
_repr_start = {'asap': T("As soon as enough players have joined"),
               'ontime': T("Wait for the join time to expire")}
_repr_press = {'all': T("Allow all"),
               'globals': T("Allow only global chat"),
               'none': T("Disable game messages")}
_repr_assign = {'random': T("Random assignment"),
                'choose': T("Every player choose its country")}
_repr_access = {'free': T("Everyone can join the game"),
                'password': T("Password-protect the game")}


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
        "phasetime": isIntInRange(5, 60*24*10),
        "jointime": isIntInRange(5, 60*24*10),
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

    labels = {
        "map": T("Variant"),
        "nplayers": T("Num. of players"),
        "bet": T("Bet amount"),
        "pottype": T("Pot type"),
        "phasetime": T("Phase period length"),
        "jointime": T("Joining period length"),
        "starton": T("Start game"),
        "buildew": T("Build everywhere"),
        "buildonstart": T("Start game with a build phase"),
        "anonymous": T("Anonymous players"),
        "presstype": T("In-game messaging"),
        "countriesassign": T("Countries assignment"),
        "countriesenabled": T("Enabled countries"),
        "access": T("Game access"),
        "maxturns": T("Maximum turns"),
        "targetsc": T("Target SCs to win")
    }

    representation = {
        "pottype": lambda value: _repr_pot[value],
        "starton": lambda value: _repr_start[value],
        "presstype": lambda value: _repr_press[value],
        "countriesassign": lambda value: _repr_assign[value]
    }

    def setup(self):
        self.entity.map.requires = inDb(self.db, self.db.maps.id, zero=None)

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
