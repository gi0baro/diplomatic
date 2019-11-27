# -*- coding: utf-8 -*-

from aioredis import Redis as _Redis
from aioredis.pool import ConnectionsPool
from contextlib import asynccontextmanager
from emmett.extensions import Extension, listen_signal


class Redis(Extension):
    def on_load(self):
        self.pool = None

    @listen_signal('after_loop')
    def build_pool(self, loop):
        self.pool = ConnectionsPool(
            f'redis://{self.app.config.redis.host}:{self.app.config.redis.port}',
            db=2,
            minsize=0,
            maxsize=128,
            create_connection_timeout=1,
            loop=loop
        )

    @asynccontextmanager
    async def ctx(self):
        connection = await self.pool.acquire()
        try:
            yield _Redis(connection)
        finally:
            self.pool.release(connection)
