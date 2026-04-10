import asyncio
import json
from PyQt6.QtCore import QThread, pyqtSignal
from websockets.asyncio.client import connect
from app.db.supabase_client import SUPABASE_URL, SUPABASE_ANON_KEY

_WS_URL = (
    SUPABASE_URL
    .replace("https://", "wss://")
    .replace("http://", "ws://")
    .rstrip("/")
    + f"/realtime/v1/websocket?apikey={SUPABASE_ANON_KEY}&vsn=1.0.0"
)


class RealtimeListener(QThread):
    # Emits "history" or "chat" depending on which channel received a broadcast
    ping = pyqtSignal(str)

    def __init__(self, access_token, refresh_token, league_id, parent=None):
        super().__init__(parent)
        self._access_token  = access_token
        self._refresh_token = refresh_token
        self._league_id     = league_id
        self._loop          = None

    def stop(self):
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.wait()

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._listen())
        except Exception as e:
            print(f"[RealtimeListener] error: {e}")
        finally:
            self._loop.close()

    async def _listen(self):
        history_topic = f"realtime:league:{self._league_id}:history"
        chat_topic    = f"realtime:league:{self._league_id}:chat"
        topics        = {history_topic: "history", chat_topic: "chat"}

        async with connect(_WS_URL) as ws:
            # Join both channels
            for ref, topic in enumerate(topics, start=1):
                await ws.send(json.dumps({
                    "topic": topic,
                    "event": "phx_join",
                    "payload": {
                        "config": {"broadcast": {"ack": False}, "private": True},
                        "access_token": self._access_token,
                    },
                    "ref": str(ref),
                }))

            async for raw in ws:
                msg   = json.loads(raw)
                topic = msg.get("topic")
                if msg.get("event") == "broadcast" and topic in topics:
                    self.ping.emit(topics[topic])
