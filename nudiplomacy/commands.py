# -*- coding: utf-8 -*-

import click
import json
import os
from . import app, db, User, SysProp, Map


@app.command()
def setup():
    with db.connection():
        SysProp.create(name="online", data={'value': False})
        db.commit()


@app.command()
@click.argument('email')
@click.argument('password')
@click.option('--username', default='admin')
def create_admin(email, password, username):
    with db.connection():
        res = User.create(
            email=email,
            password=password,
            username=username,
            is_admin=True
        )
        db.commit()
    if res.id:
        print('Created admin user with id {}'.format(res.id))
    else:
        print('Cannot create admin user due to errors: {}'.format(res.errors))


@app.command()
@click.argument('name')
def add_map(name):
    map_folder = os.path.join(app.root_path, '..', 'variants', name)
    with open(os.path.join(map_folder, '{}.json'.format(name))) as data_file:
        map_data = json.loads(data_file.read())
    with open(os.path.join(map_folder, 'map.png'), 'rb') as map_file:
        with db.connection():
            Map.create(image=map_file, **map_data)
            db.commit()


@app.command()
def create_test_data():
    with db.connection():
        for idx in range(1, 11):
            key = f'tester{idx}'
            User.create(
                email="{}@nudiplomacy.com".format(key),
                password="foobar",
                username=key)
        db.commit()


# @app.command('setup')
# def setup():
#     from yaml import load as ymlload
#     with open(app.config_path + '/setup.yml', 'r') as f:
#         rd = f.read()
#     configdata = ymlload(rd)
#     udata = dict(
#         email=configdata['email'],
#         first_name=configdata['first_name'],
#         last_name=configdata['last_name'],
#         password=Crypt()(configdata['password'])[0],
#         username=configdata['username']
#     )
#     u = auth.get_or_create_user(udata, login=False)
#     gid = auth.add_group("admin", "admin")
#     auth.add_membership(gid, u.id)
#     db.SysProp.insert(name="sys_online", data={'value': False})


# temp
# @app.command('addtester')
# def addtester():
#     db._adapter.reconnect()
#     c = db(db.User).count()
#     udata = dict(
#         email="tester"+str(c)+"@nudiplomacy.com",
#         first_name="Tester",
#         last_name=str(c),
#         password=Crypt()("imtester"+str(c))[0]
#     )
#     auth.get_or_create_user(udata, login=False)
#
