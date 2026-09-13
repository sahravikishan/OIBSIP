import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration parameters."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "chat-app-oibsip-task5-insecure-dev-key-change-in-prod")
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        os.path.join(BASE_DIR, "database", "chat.db")
    )
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max payload
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    TESTING = False
    
    # Chat app settings
    MAX_MESSAGE_LENGTH = 2000
    MAX_ROOM_NAME_LENGTH = 32
    MAX_USERNAME_LENGTH = 25
    MIN_USERNAME_LENGTH = 3
    MIN_PASSWORD_LENGTH = 6

class TestingConfig(Config):
    """Configuration for testing."""
    TESTING = True
    DATABASE_PATH = ":memory:"
    SECRET_KEY = "test-secret-key"
