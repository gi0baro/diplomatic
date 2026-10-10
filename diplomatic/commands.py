# -*- coding: utf-8 -*-

import glob
import os

import click

from . import Map, SysProp, User, app, db
from .variants import load


@app.command()
def setup():
    with db.connection():
        SysProp.create(name="online", data={"value": False})
        db.commit()


@app.command()
@click.argument("email")
@click.argument("password")
@click.option("--username", default="admin")
def create_admin(email, password, username):
    with db.connection():
        res = User.create(email=email, password=password, username=username, is_admin=True)
        db.commit()
    if res.id:
        print("Created admin user with id {}".format(res.id))
    else:
        print("Cannot create admin user due to errors: {}".format(res.errors))


@app.command()
def load_maps():
    folder = os.path.join(app.root_path, "..", "variants")
    with db.connection():
        stored = {}
        for row in Map.all().select(Map.name, Map.revision):
            stored[row.name] = max(stored.get(row.name, 0), row.revision)
        for path in sorted(glob.glob(os.path.join(folder, "*", "*.yaml"))):
            variant = load(path)
            if stored.get(variant["name"], 0) >= variant["revision"]:
                continue
            with open(os.path.join(os.path.dirname(path), "map.png"), "rb") as image:
                res = Map.create(image=image, **variant)
            if res.errors:
                raise click.ClickException(f"{path}: {res.errors}")
            print(f"Loaded {variant['name']} revision {variant['revision']}")
        db.commit()


@app.command()
def create_test_data():
    with db.connection():
        for idx in range(1, 11):
            key = f"tester{idx}"
            User.create(email="{}@diplomatic.com".format(key), password="foobar", username=key)
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
#         email="tester"+str(c)+"@diplomatic.com",
#         first_name="Tester",
#         last_name=str(c),
#         password=Crypt()("imtester"+str(c))[0]
#     )
#     auth.get_or_create_user(udata, login=False)
#
