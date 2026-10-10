# -*- coding: utf-8 -*-

from contextlib import asynccontextmanager

from emmett.extensions import Extension
from redis.asyncio import ConnectionPool, Redis as _Redis


class Redis(Extension):
    def on_load(self):
        pool = ConnectionPool(
            host=self.app.config.redis.host,
            port=self.app.config.redis.port,
            db=2,
            max_connections=128,
            socket_connect_timeout=1,
        )
        self.client = _Redis(connection_pool=pool)

    @asynccontextmanager
    async def subscribe(self, channel):
        pubsub = self.client.pubsub(ignore_subscribe_messages=True)
        await pubsub.subscribe(channel)
        try:
            yield pubsub
        finally:
            await pubsub.aclose()
