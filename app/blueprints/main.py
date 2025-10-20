from flask import Blueprint

main_bp = Blueprint("main", __name__)

@main_bp.get("/")
def index():
    # На этапе 1 просто текст. Шаблоны добавим на этапе 2.
    return "Hello, TASS!"
