from flask import Flask
from app.config import get_config
from app.blueprints.main import main_bp
from app.blueprints.settings import settings_bp
from app.blueprints.history import history_bp
from app.blueprints.assistants import assistants_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())
    app.register_blueprint(main_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(assistants_bp)

    return app

# Локальный старт: python -m tass_assistant.app  или python tass_assistant/app.py
if __name__ == "__main__":
    app = create_app()
    # host="0.0.0.0" удобно для Docker/VM; локально можно опустить
    app.run(host="0.0.0.0", port=5001)
