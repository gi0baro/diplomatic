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
            decode_responses=True,
            socket_connect_timeout=1,
        )
        self.client = _Redis(connection_pool=pool)

    @asynccontextmanager
    async def subscribe(self, *channels):
        pubsub = self.client.pubsub(ignore_subscribe_messages=True)
        try:
            await pubsub.subscribe(*channels)
            yield pubsub
        finally:
            await pubsub.aclose()
