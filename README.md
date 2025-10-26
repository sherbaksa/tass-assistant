


_____
Документация: Использование абстрактного слоя AI API
Быстрый старт
pythonfrom app.services.ai_providers import send_ai_request

# Простой запрос к модели
messages = [
    {"role": "user", "content": "Проанализируй эту новость..."}
]

result = send_ai_request(
    model_id=1,  # ID модели из БД
    messages=messages,
    temperature=0.7,
    max_tokens=1000
)

if result["success"]:
    print(f"Ответ: {result['content']}")
    print(f"Токены: {result['usage']}")
else:
    print(f"Ошибка: {result['error']}")
Структура ответа
Все провайдеры возвращают унифицированный формат:
python{
    "success": bool,           # Успешность запроса
    "content": str,            # Текст ответа от AI
    "model": str,              # Название использованной модели
    "usage": {                 # Статистика токенов
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int
    },
    "error": str,              # Сообщение об ошибке (если success=False)
    "fallback_used": bool      # True если использовалась fallback-модель
}
Работа с фабрикой провайдеров
pythonfrom app.services.ai_providers import AIProviderFactory

# Создание провайдера напрямую
provider = AIProviderFactory.create_provider(
    provider_name='openai',
    api_key='your-api-key',
    base_url=None  # опционально
)

# Создание из объекта БД
from app.models import Provider
db_provider = Provider.query.filter_by(name='openai').first()
provider = AIProviderFactory.create_from_db_provider(db_provider)

# Отправка запроса
result = provider.send_message(
    model='gpt-4o',
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=500
)
Формат сообщений
Все провайдеры используют единый формат (как в OpenAI):
pythonmessages = [
    {"role": "system", "content": "Ты — помощник редактора"},
    {"role": "user", "content": "Проанализируй новость"},
    {"role": "assistant", "content": "Конечно, давайте разберём..."},
    {"role": "user", "content": "Что ещё важно?"}
]
Поддерживаемые параметры
pythonresult = send_ai_request(
    model_id=1,
    messages=messages,
    
    # Общие параметры (все провайдеры)
    temperature=0.7,      # 0.0-1.0
    max_tokens=1000,
    
    # OpenAI-специфичные
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    
    # Google-специфичные
    top_k=40,
    
    # Управление fallback
    use_fallback=True     # Использовать резервную модель при ошибке
)
Автоматический Fallback
Если основная модель недоступна и в StageAssignment указана fallback_model_id:
pythonresult = send_ai_request(model_id=1, messages=messages)

if result.get("fallback_used"):
    print("⚠️ Использована резервная модель")
    print(f"Причина: {result['original_error']}")
