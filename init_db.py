#!/usr/bin/env python
"""Скрипт для инициализации базовых данных системы ассистентов"""
from app.app import create_app
from app.extensions import db
from app.models import Provider, AIModel, Stage


def init_assistants():
    """Инициализировать базовые данные для системы ассистентов."""
    app = create_app()
    with app.app_context():
        print("Инициализация системы ассистентов...")

        # 1. Создаём этапы обработки
        stages_data = [
            {"name": "classification", "display_name": "Классификация",
             "description": "Определение категории и типа новости", "order": 1},
            {"name": "freshness_check", "display_name": "Проверка на свежесть",
             "description": "Генерация поискового запроса для проверки актуальности", "order": 2},
            {"name": "analysis", "display_name": "Анализ", "description": "Глубокий анализ содержания новости",
             "order": 3},
            {"name": "recommendations", "display_name": "Рекомендации",
             "description": "Генерация рекомендаций по публикации", "order": 4},
        ]

        for stage_data in stages_data:
            existing = Stage.query.filter_by(name=stage_data["name"]).first()
            if not existing:
                stage = Stage(**stage_data)
                db.session.add(stage)
                print(f"  ✅ Создан этап: {stage_data['display_name']}")
            else:
                print(f"  ⏭️  Этап уже существует: {stage_data['display_name']}")

        db.session.commit()

        # 2. Создаём провайдеров (без API ключей)
        providers_data = [
            {"name": "openai", "display_name": "OpenAI"},
            {"name": "google", "display_name": "Google AI"},
            {"name": "anthropic", "display_name": "Anthropic"},
        ]

        for prov_data in providers_data:
            existing = Provider.query.filter_by(name=prov_data["name"]).first()
            if not existing:
                provider = Provider(**prov_data)
                db.session.add(provider)
                print(f"  ✅ Создан провайдер: {prov_data['display_name']}")
            else:
                print(f"  ⏭️  Провайдер уже существует: {prov_data['display_name']}")

        db.session.commit()

        # 3. Создаём базовые модели
        models_data = [
            # OpenAI
            {"provider": "openai", "name": "gpt-4o", "display_name": "GPT-4o", "api_identifier": "gpt-4o"},
            {"provider": "openai", "name": "gpt-4o-mini", "display_name": "GPT-4o Mini",
             "api_identifier": "gpt-4o-mini"},
            {"provider": "openai", "name": "o1", "display_name": "o1", "api_identifier": "o1"},
            {"provider": "openai", "name": "o1-mini", "display_name": "o1 Mini", "api_identifier": "o1-mini"},

            # Google
            {"provider": "google", "name": "gemini-pro", "display_name": "Gemini Pro", "api_identifier": "gemini-pro"},
            {"provider": "google", "name": "gemini-flash-2.0", "display_name": "Gemini Flash 2.0",
             "api_identifier": "gemini-2.0-flash-exp"},
            {"provider": "google", "name": "gemma2", "display_name": "Gemma 2", "api_identifier": "gemma-2-9b-it"},

            # Anthropic
            {"provider": "anthropic", "name": "claude-sonnet-4.5", "display_name": "Claude Sonnet 4.5",
             "api_identifier": "claude-sonnet-4-5-20250929"},
            {"provider": "anthropic", "name": "claude-opus-4", "display_name": "Claude Opus 4",
             "api_identifier": "claude-opus-4-20250514"},
            {"provider": "anthropic", "name": "claude-haiku", "display_name": "Claude Haiku",
             "api_identifier": "claude-3-5-haiku-20241022"},
        ]

        for model_data in models_data:
            provider = Provider.query.filter_by(name=model_data["provider"]).first()
            if not provider:
                print(f"  ⚠️  Провайдер {model_data['provider']} не найден для модели {model_data['name']}")
                continue

            existing = AIModel.query.filter_by(provider_id=provider.id, name=model_data["name"]).first()
            if not existing:
                model = AIModel(
                    provider_id=provider.id,
                    name=model_data["name"],
                    display_name=model_data["display_name"],
                    api_identifier=model_data["api_identifier"]
                )
                db.session.add(model)
                print(f"  ✅ Создана модель: {model_data['display_name']}")
            else:
                print(f"  ⏭️  Модель уже существует: {model_data['display_name']}")

        db.session.commit()

        print("\n✨ Инициализация завершена!")
        print("\nСледующие шаги:")
        print("1. Перейдите в Настройки → Ассистенты")
        print("2. Добавьте API ключи для провайдеров")
        print("3. Назначьте модели на этапы обработки")


if __name__ == "__main__":
    init_assistants()