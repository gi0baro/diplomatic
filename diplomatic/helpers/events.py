"""Game events over redis pub/sub.

Every event is one JSON frame `{"topic": ..., "data": ...}`; the game
websocket (`controllers/ws.py`) relays frames to the browser as they are.
Publishers never build frames themselves: they call `publish`, which returns
whatever the client's `publish` returns (a coroutine on the async client, so
request handlers `await` it).
"""

from emmett.serializers import Serializers


_json_dump = Serializers.get_for("json")


def frame(topic, data):
    return _json_dump({"topic": topic, "data": data})


def publish(client, channel, topic, data):
    return client.publish(channel, frame(topic, data))
