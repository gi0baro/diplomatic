# -*- coding: utf-8 -*-

from weppy.pipeline import Pipe
from . import app
from .helpers.system import system_property


class AppStatusPipe(Pipe):
    @property
    def _is_online(self):
        return system_property('online', default=False)

    async def pipe(self, next_pipe, **kwargs):
        if self._is_online:
            return await next_pipe(**kwargs)
        return app.render_template('offline.haml')
