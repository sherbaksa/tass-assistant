"""
Тестовый скрипт для проверки работы абстрактного слоя AI API
"""
from app.app import create_app
from app.services.ai_providers import AIProviderFactory, send_ai_request
from app.models import Provider, AIModel


def test_provider_factory():
    """Тест создания провайдеров через фабрику"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1: Проверка фабрики провайдеров")
    print("=" * 60)

    # Список доступных провайдеров
    available = AIProviderFactory.get_available_providers()
    print(f"✅ Доступные провайдеры: {', '.join(available)}")

    # Попытка создать провайдер с фейковым ключом
    try:
        provider = AIProviderFactory.create_provider(
            provider_name='openai',
            api_key='test_key_12345',
            base_url=None
        )
        print(f"✅ OpenAI провайдер создан: {type(provider).__name__}")
        print(f"   Base URL: {provider.base_url}")
    except Exception as e:
        print(f"❌ Ошибка создания провайдера: {e}")


def test_db_providers():
    """Тест загрузки провайдеров из БД"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Провайдеры из базы данных")
    print("=" * 60)

    providers = Provider.query.all()

    if not providers:
        print("⚠️  В базе данных нет провайдеров")
        return

    for db_provider in providers:
        print(f"\n📦 Провайдер: {db_provider.display_name}")
        print(f"   Имя: {db_provider.name}")
        print(f"   Активен: {'✅' if db_provider.is_active else '❌'}")
        print(f"   API ключ: {'✅ Настроен' if db_provider.api_key else '❌ Не настроен'}")

        if db_provider.api_key:
            try:
                provider = AIProviderFactory.create_from_db_provider(db_provider)
                print(f"   Класс провайдера: {type(provider).__name__}")
            except Exception as e:
                print(f"   ❌ Ошибка создания: {e}")


def test_db_models():
    """Тест загрузки моделей из БД"""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Модели AI из базы данных")
    print("=" * 60)

    models = AIModel.query.join(Provider).filter(
        AIModel.is_active == True,
        Provider.is_active == True
    ).all()

    if not models:
        print("⚠️  В базе данных нет активных моделей")
        return

    for model in models:
        print(f"\n🤖 Модель: {model.display_name}")
        print(f"   ID: {model.id}")
        print(f"   Провайдер: {model.provider.display_name}")
        print(f"   API идентификатор: {model.api_identifier}")
        print(f"   Активна: {'✅' if model.is_active else '❌'}")


def test_send_request():
    """Тест отправки реального запроса (если настроены API ключи)"""
    print("\n" + "=" * 60)
    print("ТЕСТ 4: Тестовый запрос к AI (если настроены ключи)")
    print("=" * 60)

    # Ищем первую активную модель с настроенным API ключом
    model = AIModel.query.join(Provider).filter(
        AIModel.is_active == True,
        Provider.is_active == True,
        Provider.api_key.isnot(None)
    ).first()

    if not model:
        print("⚠️  Нет активных моделей с настроенным API ключом")
        print("   Настройте API ключи через веб-интерфейс: /assistants/providers")
        return

    print(f"\n🚀 Отправляем тестовый запрос к: {model.display_name}")

    messages = [
        {"role": "user", "content": "Скажи 'привет' одним словом"}
    ]

    try:
        result = send_ai_request(
            model_id=model.id,
            messages=messages,
            max_tokens=50,
            temperature=0.7
        )

        print(f"\n{'=' * 60}")
        if result["success"]:
            print("✅ ЗАПРОС УСПЕШЕН!")
            print(f"   Модель: {result['model']}")
            print(f"   Ответ: {result['content']}")
            print(f"   Использование токенов: {result['usage']}")
            if result.get('fallback_used'):
                print(f"   ⚠️  Использован fallback. Оригинальная ошибка: {result.get('original_error')}")
        else:
            print("❌ ЗАПРОС НЕУСПЕШЕН")
            print(f"   Ошибка: {result['error']}")

    except Exception as e:
        print(f"❌ Исключение при запросе: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        print("\n" + "🔬 ТЕСТИРОВАНИЕ АБСТРАКТНОГО СЛОЯ AI API ".center(60, "="))

        test_provider_factory()
        test_db_providers()
        test_db_models()
        test_send_request()

        print("\n" + "=" * 60)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 60 + "\n")