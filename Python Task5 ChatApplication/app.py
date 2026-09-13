import os
import sys
from flask import Flask
from flask_socketio import SocketIO
from config import Config
from database.db import init_db
from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from sockets.events import register_socket_events

def create_app(config_class=Config):
    """Application factory for Flask and Socket.IO."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database schema and seed default rooms
    init_db(app.config["DATABASE_PATH"])

    # Register HTTP Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    # Security response headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Initialize Flask-SocketIO
    # Note: async_mode='threading' is reliable across all OS platforms without gevent/eventlet
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        manage_session=False,
        async_mode="threading"
    )

    # Register WebSocket real-time events
    register_socket_events(socketio)

    return app, socketio

# Top-level application instances for standard WSGI/CLI execution
app, socketio = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")

    print("=" * 60)
    print("   OIBSIP TASK 5: ADVANCED REAL-TIME CHAT APPLICATION")
    print("=" * 60)
    print(f" [+] Server starting on: http://{host}:{port}")
    print(f" [+] Real-time engine:   Flask-SocketIO (threading)")
    print(f" [+] Database:           SQLite ({app.config['DATABASE_PATH']})")
    print(f" [+] Password Security:  Werkzeug PBKDF2-HMAC-SHA256")
    print(f" [!] Notice:             Messages stored in SQLite (not E2E encrypted)")
    print("=" * 60)

    socketio.run(app, host=host, port=port, debug=app.config["DEBUG"], allow_unsafe_werkzeug=True)
