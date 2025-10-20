import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

class DevConfig(Config):
    ENV = "development"

class ProdConfig(Config):
    DEBUG = False
    ENV = "production"

def get_config():
    # По умолчанию dev-конфиг, можно переключать переменной окружения
    env = os.getenv("FLASK_ENV", "development").lower()
    return ProdConfig if env == "production" else DevConfig
