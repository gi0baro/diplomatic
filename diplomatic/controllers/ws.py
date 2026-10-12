from emmett import session, websocket
from emmett.http import HTTPResponse

from .. import GameRole, app, db, sessions


ws = app.module(__name__, "ws", url_prefix="ws")
#: no `db.pipe`: it would keep a connection open for the socket's lifetime; the db is used only at opening
ws.pipeline = [sessions]


async def _player_role(gid):
    if not session.auth or not session.auth.user:
        return None
    async with db.connection():
        role = GameRole.where(lambda m: (m.game == gid) & (m.user == session.auth.user.id)).select().first()
    return role.id if role else None


@ws.websocket("/game/<int:gid>")
async def game(gid):
    #: frames are built by `helpers.events`; the socket relays them as they are
    role_id = await _player_role(gid)
    if not role_id:
        raise HTTPResponse(403)
    channels = (f"game:{gid}:state", f"game:{gid}:players", f"chat:{role_id}:messages")
    async with app.ext.Redis.subscribe(*channels) as channel:
        await websocket.accept()
        async for message in channel.listen():
            await websocket.send(message["data"])
