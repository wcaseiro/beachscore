from flask import request
from flask_socketio import SocketIO, emit, join_room


socketio = SocketIO()


class SocketManager:
    def __init__(self, socketio_instance, courts):
        self.socketio = socketio_instance
        self.courts = courts
        self._registered = False

    def register_handlers(self):
        if self._registered:
            return

        @self.socketio.on("connect")
        def on_connect():
            court_id = request.args.get("court_id", "arena-1")
            join_room(court_id)
            emit("state", self.courts.state(court_id))

        @self.socketio.on("join_court")
        def on_join(data):
            court_id = (data or {}).get("court_id", "arena-1")
            join_room(court_id)
            emit("state", self.courts.state(court_id))

        self._registered = True

    def emit_state(self, court_id, state):
        self.socketio.emit("state", state, room=court_id)
        if court_id == "arena-1":
            self.socketio.emit("state", state)
