from emmett import session, websocket
from emmett.http import HTTPResponse

from .. import GameRole, app, db, sessions


ws = app.module(__name__, "ws", url_prefix="ws")
ws.pipeline = [sessions]

WATCH_TTL = 60
WATCH_REFRESH = 20


async def _player_role(gid):
    if not session.auth or not session.auth.user:
        return None
    async with db.connection():
        role = GameRole.current().where(lambda m: (m.game == gid) & (m.user == session.auth.user.id)).select().first()
    return role.id if role else None


@ws.websocket("/game/<str:gid>")
async def game(gid):
    role_id = await _player_role(gid)
    if not role_id:
        raise HTTPResponse(403)
    channels = (f"game:{gid}:state", f"game:{gid}:players", f"chat:{role_id}:messages")
    client = app.ext.Redis.client
    key = f"game:{gid}:watching:{session.auth.user.id}"
    async with app.ext.Redis.subscribe(*channels) as channel:
        await websocket.accept()
        while True:
            await client.set(key, 1, ex=WATCH_TTL)
            message = await channel.get_message(timeout=WATCH_REFRESH)
            if message:
                await websocket.send(message["data"])
