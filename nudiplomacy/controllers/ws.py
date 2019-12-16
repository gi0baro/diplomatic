# -*- coding: utf-8 -*-

from emmett import websocket

from .. import app

ws = app.module(__name__, 'ws', url_prefix='ws')


@ws.websocket('/game/<int:gid>/state')
async def game_state(gid):
    async with app.ext.Redis.ctx() as redis:
        channel, = await redis.subscribe(f'game:{gid}:state')
        await websocket.accept()

        async for message in channel.iter():
            await websocket.send(message)
            break


@ws.websocket('/chat/<int:player_id>/messages')
async def chat_messages(player_id):
    async with app.ext.Redis.ctx() as redis:
        channel, = await redis.subscribe(f'chat:{player_id}:messages')
        await websocket.accept()

        async for message in channel.iter():
            await websocket.send(message)
