from rq import Queue, Connection, Worker
from weppy.validators import Crypt
from nudiplomacy import app, db, auth, redis
from nudiplomacy.helpers.scheduler import Scheduler


@app.command('setup')
def setup():
    from yaml import load as ymlload
    f = open(app.config_path+'/setup.yml')
    rd = f.read()
    f.close()
    configdata = ymlload(rd)
    udata = dict(
        email=configdata['email'],
        first_name=configdata['first_name'],
        last_name=configdata['last_name'],
        password=Crypt()(configdata['password'])[0],
        username=configdata['username']
    )
    u = auth.get_or_create_user(udata, login=False)
    gid = auth.add_group("admin", "admin")
    auth.add_membership(gid, u.id)
    db.SysProp.insert(name="sys_online", data={'value': False})


# temp
@app.command('addtester')
def addtester():
    db._adapter.reconnect()
    c = db(db.auth_user.id > 0).count()
    udata = dict(
        email="tester"+str(c)+"@nudiplomacy.com",
        first_name="Tester",
        last_name=str(c),
        password=Crypt()("imtester"+str(c))[0]
    )
    auth.get_or_create_user(udata, login=False)
#


@app.command('gameman')
def schedule():
    s = Scheduler()
    s.run()


@app.command('queue_def')
def _q_default():
    with Connection(connection=redis):
        qs = [Queue('default')]
        w = Worker(qs)
        w.work()


@app.command('queue_open')
def _q_open():
    with Connection(connection=redis):
        qs = [Queue('open')]
        w = Worker(qs)
        w.work()


@app.command('queue_proc')
def _q_process():
    with Connection(connection=redis):
        qs = [Queue('process')]
        w = Worker(qs)
        w.work()


@app.command('queue_misc')
def _q_misc():
    with Connection(connection=redis):
        qs = [Queue('misc')]
        w = Worker(qs)
        w.work()
