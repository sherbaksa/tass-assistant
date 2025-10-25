"""
Сервис для работы с AI провайдерами (OpenAI, Google, Anthropic)
"""
import json
import requests
from typing import Dict, Tuple


class AIProviderError(Exception):
    """Базовое исключение для ошибок провайдеров"""
    pass


def test_openai_connection(api_key: str, base_url: str = None) -> Tuple[bool, str]:
    """
    Тестирование подключения к OpenAI API

    Returns:
        (success: bool, message: str)
    """
    if not api_key:
        return False, "API ключ не указан"

    url = base_url or "https://api.openai.com/v1"
    endpoint = f"{url}/models"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(endpoint, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            models_count = len(data.get('data', []))
            return True, f"✅ Подключение успешно! Доступно моделей: {models_count}"
        elif response.status_code == 401:
            return False, "❌ Неверный API ключ"
        elif response.status_code == 429:
            return False, "❌ Превышен лимит запросов"
        else:
            return False, f"❌ Ошибка {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return False, "❌ Превышено время ожидания ответа"
    except requests.exceptions.ConnectionError:
        return False, f"❌ Ошибка подключения к {url}"
    except Exception as e:
        return False, f"❌ Неизвестная ошибка: {str(e)}"


def test_google_connection(api_key: str, base_url: str = None) -> Tuple[bool, str]:
    """
    Тестирование подключения к Google AI (Gemini) API

    Returns:
        (success: bool, message: str)
    """
    if not api_key:
        return False, "API ключ не указан"

    url = base_url or "https://generativelanguage.googleapis.com"
    # Список моделей
    endpoint = f"{url}/v1beta/models?key={api_key}"

    try:
        response = requests.get(endpoint, timeout=10)

        if response.status_code == 200:
            data = response.json()
            models_count = len(data.get('models', []))
            return True, f"✅ Подключение успешно! Доступно моделей: {models_count}"
        elif response.status_code == 400:
            error_message = response.json().get('error', {}).get('message', 'Unknown error')
            return False, f"❌ Неверный запрос: {error_message}"
        elif response.status_code == 403:
            return False, "❌ Неверный API ключ или доступ запрещен"
        else:
            return False, f"❌ Ошибка {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return False, "❌ Превышено время ожидания ответа"
    except requests.exceptions.ConnectionError:
        return False, f"❌ Ошибка подключения к {url}"
    except Exception as e:
        return False, f"❌ Неизвестная ошибка: {str(e)}"


def test_anthropic_connection(api_key: str, base_url: str = None) -> Tuple[bool, str]:
    """
    Тестирование подключения к Anthropic (Claude) API

    Returns:
        (success: bool, message: str)
    """
    if not api_key:
        return False, "API ключ не указан"

    url = base_url or "https://api.anthropic.com"
    # Anthropic не предоставляет endpoint для списка моделей,
    # поэтому делаем минимальный запрос к API
    endpoint = f"{url}/v1/messages"

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    # Минимальный тестовый запрос
    payload = {
        "model": "claude-3-5-haiku-20241022",  # Самая дешевая модель для теста
        "max_tokens": 10,
        "messages": [
            {"role": "user", "content": "Hi"}
        ]
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)

        if response.status_code == 200:
            return True, "✅ Подключение успешно! API ключ валиден"
        elif response.status_code == 401:
            return False, "❌ Неверный API ключ"
        elif response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            # Если ошибка не связана с аутентификацией, ключ валиден
            if 'authentication' not in error_message.lower():
                return True, f"✅ API ключ валиден (тестовая модель недоступна, но ключ работает)"
            return False, f"❌ {error_message}"
        elif response.status_code == 429:
            return False, "❌ Превышен лимит запросов"
        else:
            return False, f"❌ Ошибка {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return False, "❌ Превышено время ожидания ответа"
    except requests.exceptions.ConnectionError:
        return False, f"❌ Ошибка подключения к {url}"
    except Exception as e:
        return False, f"❌ Неизвестная ошибка: {str(e)}"


def test_provider_connection(provider_name: str, api_key: str, additional_config: str = None) -> Tuple[bool, str]:
    """
    Универсальная функция тестирования подключения к провайдеру

    Args:
        provider_name: Имя провайдера (openai, google, anthropic)
        api_key: API ключ
        additional_config: JSON-строка с дополнительной конфигурацией (base_url и т.д.)

    Returns:
        (success: bool, message: str)
    """
    # Извлекаем base_url из конфигурации
    base_url = None
    if additional_config:
        try:
            config = json.loads(additional_config)
            base_url = config.get('base_url')
        except json.JSONDecodeError:
            pass

    # Вызываем соответствующую функцию
    if provider_name == 'openai':
        return test_openai_connection(api_key, base_url)
    elif provider_name == 'google':
        return test_google_connection(api_key, base_url)
    elif provider_name == 'anthropic':
        return test_anthropic_connection(api_key, base_url)
    else:
        return False, f"❌ Неизвестный провайдер: {provider_name}"