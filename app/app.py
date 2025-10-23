from flask import Flask
from app.config import get_config

# существующие блюпринты
from app.blueprints.main import main_bp
from app.blueprints.settings import settings_bp
from app.blueprints.history import history_bp
from app.blueprints.assistants import assistants_bp

# новые расширения и блюпринт аутентификации
from app.extensions import db, migrate, login_manager, mail, csrf
from app.auth.routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Регистрация блюпринтов
    app.register_blueprint(main_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(assistants_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # --- временный debug-route: показывает, попали ли значения в app.config (не выводит сам ключ) ---
    @app.route("/_debug_env")
    def _debug_env():
        return {
            "MAIL_BACKEND": app.config.get("MAIL_BACKEND"),
            "HAS_SENDGRID_KEY": bool(app.config.get("SENDGRID_API_KEY")),
            "MAIL_DEFAULT_SENDER": app.config.get("MAIL_DEFAULT_SENDER"),
            "ENV": app.config.get("ENV"),
            "DEBUG": app.config.get("DEBUG")
        }

    return app  # ← ВАЖНО: 4 пробела отступа, внутри функции create_app()

# Локальный старт
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001)
