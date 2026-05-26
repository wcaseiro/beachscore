from beachscore import create_app
from beachscore.websocket import socketio
from pathlib import Path


app = create_app()


if __name__ == "__main__":
    ssl_args = {}
    if Path("cert.pem").exists() and Path("key.pem").exists():
        ssl_args = {"certfile": "cert.pem", "keyfile": "key.pem"}

    socketio.run(app, host="0.0.0.0", port=5000, **ssl_args)
