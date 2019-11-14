# -*- coding: utf-8 -*-

from weppy import websocket

from .. import app

ws = app.module(__name__, 'ws', url_prefix='ws')


@ws.websocket('/game/<int:gid>/state')
async def game_state(gid):
    async with app.ext.Redis.ctx() as redis:
        channel, = await redis.subscribe(f'game:{gid}:state')
        await websocket.accept()

        async for message in channel.iter():
            app.log.debug(message)
            await websocket.send(message)
            break
