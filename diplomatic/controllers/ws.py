# -*- coding: utf-8 -*-

from emmett import websocket

from .. import app


ws = app.module(__name__, "ws", url_prefix="ws")


@ws.websocket("/game/<int:gid>/state")
async def game_state(gid):
    async with app.ext.Redis.subscribe(f"game:{gid}:state") as channel:
        await websocket.accept()

        async for message in channel.listen():
            await websocket.send(message["data"])
            break


@ws.websocket("/chat/<int:player_id>/messages")
async def chat_messages(player_id):
    async with app.ext.Redis.subscribe(f"chat:{player_id}:messages") as channel:
        await websocket.accept()

        async for message in channel.listen():
            await websocket.send(message["data"])
