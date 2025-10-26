from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.pipeline_processor import PipelineProcessor
import json

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Главная страница"""
    stages = []
    if current_user.is_authenticated:
        # Получаем список доступных этапов для формы
        stages = PipelineProcessor.get_available_stages()

    return render_template("main/index.html", title="Главная", stages=stages)


@main_bp.route("/process", methods=["POST"])
@login_required
def process_news():
    """
    Обработка новости через конвейер этапов

    Ожидает JSON:
    {
        "news_text": "текст новости",
        "stage_ids": [1, 2, 3]
    }

    Возвращает JSON с результатами обработки
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Не переданы данные"
            }), 400

        news_text = data.get("news_text", "").strip()
        stage_ids = data.get("stage_ids", [])

        # Валидация
        if not news_text:
            return jsonify({
                "success": False,
                "error": "Текст новости не может быть пустым"
            }), 400

        if not stage_ids or not isinstance(stage_ids, list):
            return jsonify({
                "success": False,
                "error": "Не выбраны этапы обработки"
            }), 400

        # Преобразуем stage_ids в int
        try:
            stage_ids = [int(sid) for sid in stage_ids]
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Некорректные ID этапов"
            }), 400

        # Обрабатываем новость через конвейер
        result = PipelineProcessor.process_news(
            user_id=current_user.id,
            news_text=news_text,
            stage_ids=stage_ids
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Ошибка сервера: {str(e)}"
        }), 500