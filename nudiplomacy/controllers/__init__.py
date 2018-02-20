# -*- coding: utf-8 -*-

from weppy import url, redirect
from weppy.pipeline import RequirePipe
from .. import app, auth
from ..contexts import BaseContext
from ..pipes import AppStatusPipe


auth_routes = auth.module(__name__, url_prefix='account')
auth_routes.injectors = [BaseContext()]

front = app.module(__name__, 'front')
front.pipeline = [AppStatusPipe()]
front.injectors = [BaseContext()]

authenticated = front.module(__name__, 'auth')
authenticated.pipeline = [RequirePipe(auth.is_logged, url('auth.login'))]


@auth_routes.after_login
def after_login(form):
    redirect(url('front.games.index'))
