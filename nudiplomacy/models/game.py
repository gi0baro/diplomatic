import json
import random
from datetime import timedelta
from weppy import request, session, T, sdict
from weppy.dal import Field, Model, before_insert, after_insert, modelmethod, \
    fieldmethod
from weppy.validators import inDb, isntEmpty, inSet, isIntInRange
from nudiplomacy import app
from nudiplomacy.helpers.widgets import games_map, games_nplayers, games_ce, \
    games_phasetime, games_jointime, games_bet
from nudiplomacy.helpers.mongo import longToObjid

_repr_lang = {'en': "English", 'it': "Italiano"}
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
        Field("owner", "reference auth_user",
              default=lambda: session.auth.user.id),
        Field("map", "reference maps"),
        Field("name"),
        Field("lang"),
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
        Field("open", "boolean", default=True),
        Field("slots", "json", default="[]"),
        Field("ready", "boolean", default=False),
        Field("created", "datetime", default=lambda: request.now),
        Field("processed", "datetime", default=lambda: request.now),
        Field("next", "datetime"),
        Field("countries", "json"),
        Field("phases", "json")
    ]

    validators = {
        "name": isntEmpty(),
        "lang": inSet(app.config.langs, zero=None),
        "bet": isIntInRange(1, 150),
        "pottype": inSet(["wta", "ppsc"], zero=None),
        "phasetime": isIntInRange(10, 60*24*10),
        "jointime": isIntInRange(10, 60*24*10),
        "starton": inSet(["asap", "ontime"], zero=None),
        "presstype": inSet(["all", "globals", "none"], zero=None),
        "countriesassign": inSet(["random", "choose"], zero=None),
        "access": inSet(["free", "password"], zero=None)
    }

    visibility = {
        "owner": (False, False),
        "status": (False, False),
        "active": (False, False),
        "open": (False, False),
        "slots": (False, False),
        "created": (False, False),
        "processed": (False, False),
        "next": (False, False),
        "ready": (False, False),
        "phases": (False, False),
    }

    labels = {
        "map": T("Variant"),
        "lang": T("Language"),
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

    comments = {
        "maxturns": T("Limit how many turns are played."),
        "countriesenabled": T("You can select which countries will be " +
                              "available for assignment or can be chosen by " +
                              "players. Remind that if you selected the " +
                              "maximum no. of players, this setting has no " +
                              "effect, all the countries will be available.")
    }

    representation = {
        "lang": lambda value: _repr_lang[value],
        "pottype": lambda value: _repr_pot[value],
        "starton": lambda value: _repr_start[value],
        "presstype": lambda value: _repr_press[value],
        "countriesassign": lambda value: _repr_assign[value],
        "access": lambda value: _repr_access[value]
    }

    widgets = {
        "map": lambda field, value: games_map(field, value),
        "nplayers": lambda field, value: games_nplayers(field, value),
        "bet": lambda field, value: games_bet(field, value),
        "countriesenabled": lambda field, value: games_ce(field, value),
        "phasetime": lambda field, value: games_phasetime(field, value),
        "jointime": lambda field, value: games_jointime(field, value)
    }

    def setup(self):
        self.entity.map.requires = inDb(self.db, self.db.maps.id, zero=None)

    @fieldmethod('playercountry')
    def get_country(self, row):
        uid = session.auth.user.id if session.auth else None
        if not uid:
            return None
        #from nudiplomacy.helpers.mongo import objidToLong
        poid = longToObjid(uid)
        #for k, v in row.games.countries.items():
        #    if objidToLong(v) == uid:
        #        return k
        for el in row.games.countries:
            if el['player'] == poid:
                return el['country']
        return None

    @fieldmethod('playersin')
    def get_players_in(self, row):
        #n = 0
        #for k, v in row.games.countries.items():
        #    if v is not None:
        #        n += 1
        return len(row.games.countries)

    @fieldmethod('isjoinable')
    def is_joinable(self, row):
        if row.games.playersin() != row.games.nplayers:
            return True
        return False

    @fieldmethod('timetonext')
    def get_next_timer(self, row):
        timeleft = int((row.games.next-request.now).total_seconds())
        timerdata = sdict(d=0, h=0, m=0, s=0)
        if timeleft > 0:
            timerdata.d = timeleft/(60*60*24)
            timerdata.h = (timeleft/(60*60)) % 24
            timerdata.m = (timeleft/60) % 60
            timerdata.s = timeleft % 60
        return timerdata

    @before_insert
    def setup_game(self, fields):
        # build countries based on selected preferences
        #ce = json.loads(fields['countriesenabled'])
        ce = fields['countriesenabled']
        fields['countriesenabled'] = json.dumps(fields['countriesenabled'])
        random.shuffle(ce)
        countrylist = ce[:fields['nplayers']]
        #fields['countries'] = {}
        #for name in countrylist:
        #    fields['countries'][name] = None
        if fields['countriesassign'] == "random":
            chosen = countrylist[0]
        else:
            chosen = fields['countries']['me']
        fields['countries'] = []
        #fields['countries'][chosen] = longToObjid(session.auth.user.id)
        fields['countries'].append({
            'country': chosen,
            'player': longToObjid(session.auth.user.id)})
        slots = list(countrylist)
        slots.remove(chosen)
        fields['slots'] = slots
        # init phases
        fields['phases'] = json.dumps(
            [{"type": "pre-game", "countries": countrylist}])
        #: set next time
        fields['next'] = request.now + timedelta(minutes=fields['phasetime'])

    @after_insert
    def get_owner_credits(self, fields, gid):
        self.db.UserData(user=fields['owner']).update(
            credits=self.db.Userdata.credits-fields['bet']
        )

    @after_insert
    def add_global_chat(self, fields, gid):
        if fields['presstype'] != "none":
            self.db.Chat.insert(game=gid, users='["all"]')


class Player(Model):
    tablename = "players"

    fields = [
        Field("user", "reference auth_user"),
        Field("game", "reference games"),
        Field("country", "string")
    ]


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
            return sdict(data={})
        rv = db((entity.game == gid) & (entity.player == uid)).select().first()
        if not rv:
            return sdict(data={})
        return sdict(data=rv.data, ready=rv.ready)


class Chat(Model):
    tablename = "chats"

    fields = [
        Field("game", "reference games"),
        Field("open", "boolean", default=True),
        Field("users", "json"),
        Field("messages", "json", default="[]")
    ]
