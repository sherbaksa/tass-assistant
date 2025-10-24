import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../tass-assistant
DEFAULT_SQLITE = PROJECT_ROOT / "app.db"

class Config:
    # базовое
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # БД: абсолютный путь к SQLite, чтобы не зависеть от working dir IDE
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE.as_posix()}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # почта
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "25"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "0") == "1"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "0") == "1"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com")

    MAIL_BACKEND = os.getenv("MAIL_BACKEND", "smtp")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    # токены
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "dev-salt")

    # регистрация
    REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "1") == "1"

    # cookies / сессии
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1") == "1"

class DevConfig(Config):
    ENV = "development"
    SESSION_COOKIE_SECURE = False

class ProdConfig(Config):
    DEBUG = False
    ENV = "production"

def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return ProdConfig if env == "production" else DevConfig
