import os


def create_app(config=None):
    from flask import Flask

    from .api import api_bp
    from .courts import CourtManager
    from .storage import SQLiteStore
    from .views import views_bp
    from .voice import VoiceService
    from .websocket import SocketManager, socketio

    template_folder = os.path.join(os.path.dirname(__file__), "..", "templates")
    app = Flask(__name__, instance_relative_config=True, template_folder=template_folder)
    app.config.update(
        DATABASE_PATH=os.path.join(app.instance_path, "beachscore.sqlite3"),
        SECRET_KEY="beachscore-dev",
    )

    if config:
        app.config.update(config)

    os.makedirs(app.instance_path, exist_ok=True)

    store = SQLiteStore(app.config["DATABASE_PATH"])
    store.init_db()

    court_manager = CourtManager(store)
    voice_service = VoiceService(court_manager)
    websocket_manager = SocketManager(socketio, court_manager)

    app.extensions["beachscore_store"] = store
    app.extensions["beachscore_courts"] = court_manager
    app.extensions["beachscore_voice"] = voice_service
    app.extensions["beachscore_websocket"] = websocket_manager

    socketio.init_app(app, cors_allowed_origins="*")
    websocket_manager.register_handlers()

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
