"""
Сервис для работы с AI провайдерами (OpenAI, Google, Anthropic)
"""
import json
import requests
from typing import Dict, Tuple
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


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


# ============================================================================
# Абстрактный слой API для работы с AI провайдерами
# ============================================================================

class BaseAIProvider(ABC):
    """
    Базовый абстрактный класс для всех AI провайдеров
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, additional_config: Optional[Dict] = None):
        """
        Args:
            api_key: API ключ провайдера
            base_url: Базовый URL (опционально, для кастомных endpoint'ов)
            additional_config: Дополнительная конфигурация (dict)
        """
        self.api_key = api_key
        self.base_url = base_url or self.get_default_base_url()
        self.additional_config = additional_config or {}
        self.timeout = self.additional_config.get('timeout', 30)

    @abstractmethod
    def get_default_base_url(self) -> str:
        """Возвращает базовый URL по умолчанию для провайдера"""
        pass

    @abstractmethod
    def send_message(self,
                     model: str,
                     messages: List[Dict[str, str]],
                     **kwargs) -> Dict[str, Any]:
        """
        Отправить сообщение модели

        Args:
            model: Идентификатор модели (api_identifier из БД)
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            **kwargs: Дополнительные параметры (temperature, max_tokens, etc.)

        Returns:
            Dict с ответом модели в унифицированном формате:
            {
                "success": bool,
                "content": str,  # текст ответа
                "model": str,    # использованная модель
                "usage": dict,   # статистика использования токенов
                "error": str     # сообщение об ошибке (если success=False)
            }
        """
        pass

    def validate_config(self) -> tuple[bool, str]:
        """
        Проверить корректность конфигурации

        Returns:
            (success: bool, message: str)
        """
        if not self.api_key:
            return False, "API ключ не указан"
        return True, "Конфигурация корректна"


class OpenAIProvider(BaseAIProvider):
    """
    Провайдер для OpenAI API (GPT-4, GPT-3.5, etc.)
    """

    def get_default_base_url(self) -> str:
        return "https://api.openai.com/v1"

    def send_message(self,
                     model: str,
                     messages: List[Dict[str, str]],
                     **kwargs) -> Dict[str, Any]:
        """
        Отправить сообщение в OpenAI API
        """
        endpoint = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Параметры запроса
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
        }

        # Дополнительные параметры если есть
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            payload["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            payload["presence_penalty"] = kwargs["presence_penalty"]

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "content": data["choices"][0]["message"]["content"],
                    "model": data["model"],
                    "usage": data.get("usage", {}),
                    "error": None
                }
            else:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get("message", response.text[:200])

                return {
                    "success": False,
                    "content": None,
                    "model": model,
                    "usage": {},
                    "error": f"OpenAI API Error {response.status_code}: {error_message}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": "Превышено время ожидания ответа"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": f"Ошибка подключения к {self.base_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": f"Неизвестная ошибка: {str(e)}"
            }


class GoogleProvider(BaseAIProvider):
    """
    Провайдер для Google AI (Gemini)
    """

    def get_default_base_url(self) -> str:
        return "https://generativelanguage.googleapis.com"

    def send_message(self,
                     model: str,
                     messages: List[Dict[str, str]],
                     **kwargs) -> Dict[str, Any]:
        """
        Отправить сообщение в Google AI API

        Note: Google Gemini использует другой формат сообщений
        """
        endpoint = f"{self.base_url}/v1beta/models/{model}:generateContent"

        # Google использует API key в query параметрах
        params = {"key": self.api_key}

        headers = {
            "Content-Type": "application/json"
        }

        # Конвертируем OpenAI-формат сообщений в Google-формат
        contents = self._convert_messages_to_google_format(messages)

        # Параметры генерации
        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "maxOutputTokens": kwargs.get("max_tokens", 1000),
        }

        if "top_p" in kwargs:
            generation_config["topP"] = kwargs["top_p"]
        if "top_k" in kwargs:
            generation_config["topK"] = kwargs["top_k"]

        payload = {
            "contents": contents,
            "generationConfig": generation_config
        }

        try:
            response = requests.post(
                endpoint,
                params=params,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()

                # Извлекаем текст ответа
                content = ""
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        content = candidate["content"]["parts"][0].get("text", "")

                # Извлекаем usage если есть
                usage = {}
                if "usageMetadata" in data:
                    usage = {
                        "prompt_tokens": data["usageMetadata"].get("promptTokenCount", 0),
                        "completion_tokens": data["usageMetadata"].get("candidatesTokenCount", 0),
                        "total_tokens": data["usageMetadata"].get("totalTokenCount", 0)
                    }

                return {
                    "success": True,
                    "content": content,
                    "model": model,
                    "usage": usage,
                    "error": None
                }
            else:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get("message", response.text[:200])

                return {
                    "success": False,
                    "content": None,
                    "model": model,
                    "usage": {},
                    "error": f"Google AI API Error {response.status_code}: {error_message}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": "Превышено время ожидания ответа"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": f"Ошибка подключения к {self.base_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": f"Неизвестная ошибка: {str(e)}"
            }

    def _convert_messages_to_google_format(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """
        Конвертирует OpenAI-формат сообщений в Google Gemini формат

        OpenAI: [{"role": "user", "content": "text"}]
        Google: [{"role": "user", "parts": [{"text": "text"}]}]
        """
        google_messages = []

        for msg in messages:
            role = msg["role"]
            # Google использует "user" и "model" вместо "assistant"
            if role == "assistant":
                role = "model"

            google_messages.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        return google_messages


class AnthropicProvider(BaseAIProvider):
    """
    Провайдер для Anthropic API (Claude)
    """

    def get_default_base_url(self) -> str:
        return "https://api.anthropic.com"

    def send_message(self,
                     model: str,
                     messages: List[Dict[str, str]],
                     **kwargs) -> Dict[str, Any]:
        """
        Отправить сообщение в Anthropic API
        """
        endpoint = f"{self.base_url}/v1/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Anthropic требует отдельно system prompt
        system_prompt = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append(msg)

        # Параметры запроса
        payload = {
            "model": model,
            "messages": user_messages,
            "max_tokens": kwargs.get("max_tokens", 1000),
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Дополнительные параметры
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            payload["top_k"] = kwargs["top_k"]

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()

                # Извлекаем текст ответа
                content = ""
                if "content" in data and len(data["content"]) > 0:
                    content = data["content"][0].get("text", "")

                # Извлекаем usage
                usage = {}
                if "usage" in data:
                    usage = {
                        "prompt_tokens": data["usage"].get("input_tokens", 0),
                        "completion_tokens": data["usage"].get("output_tokens", 0),
                        "total_tokens": data["usage"].get("input_tokens", 0) + data["usage"].get("output_tokens", 0)
                    }

                return {
                    "success": True,
                    "content": content,
                    "model": data.get("model", model),
                    "usage": usage,
                    "error": None
                }
            else:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get("message", response.text[:200])

                return {
                    "success": False,
                    "content": None,
                    "model": model,
                    "usage": {},
                    "error": f"Anthropic API Error {response.status_code}: {error_message}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": "Превышено время ожидания ответа"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": f"Ошибка подключения к {self.base_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": f"Неизвестная ошибка: {str(e)}"
            }


class AIProviderFactory:
    """
    Фабрика для создания провайдеров AI
    """

    _providers = {
        'openai': OpenAIProvider,
        'google': GoogleProvider,
        'anthropic': AnthropicProvider,
    }

    @classmethod
    def create_provider(cls,
                        provider_name: str,
                        api_key: str,
                        base_url: Optional[str] = None,
                        additional_config: Optional[Dict] = None) -> BaseAIProvider:
        """
        Создать провайдер по имени

        Args:
            provider_name: Имя провайдера (openai, google, anthropic)
            api_key: API ключ
            base_url: Базовый URL (опционально)
            additional_config: Дополнительная конфигурация

        Returns:
            Экземпляр провайдера

        Raises:
            AIProviderError: Если провайдер не найден
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise AIProviderError(f"Неизвестный провайдер: {provider_name}")

        provider_class = cls._providers[provider_name]
        return provider_class(api_key, base_url, additional_config)

    @classmethod
    def create_from_db_provider(cls, db_provider) -> BaseAIProvider:
        """
        Создать провайдер из объекта БД Provider

        Args:
            db_provider: Объект модели Provider из БД

        Returns:
            Экземпляр провайдера
        """
        # Парсим additional_config если есть
        additional_config = None
        base_url = None

        if db_provider.additional_config:
            try:
                additional_config = json.loads(db_provider.additional_config)
                base_url = additional_config.get('base_url')
            except json.JSONDecodeError:
                pass

        return cls.create_provider(
            provider_name=db_provider.name,
            api_key=db_provider.api_key,
            base_url=base_url,
            additional_config=additional_config
        )

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Получить список доступных провайдеров"""
        return list(cls._providers.keys())


def send_ai_request(model_id: int,
                    messages: List[Dict[str, str]],
                    use_fallback: bool = True,
                    **kwargs) -> Dict[str, Any]:
    """
    Отправить запрос к AI модели с поддержкой fallback

    Args:
        model_id: ID модели из БД (AIModel.id)
        messages: Список сообщений в формате [{"role": "user", "content": "..."}]
        use_fallback: Использовать fallback-модель при ошибке
        **kwargs: Дополнительные параметры (temperature, max_tokens, etc.)

    Returns:
        Dict с результатом запроса
    """
    from app.models import AIModel, Provider

    # Загружаем модель из БД
    model = AIModel.query.get(model_id)
    if not model:
        return {
            "success": False,
            "content": None,
            "model": None,
            "usage": {},
            "error": f"Модель с ID {model_id} не найдена"
        }

    # Проверяем активность модели и провайдера
    if not model.is_active or not model.provider.is_active:
        return {
            "success": False,
            "content": None,
            "model": model.api_identifier,
            "usage": {},
            "error": "Модель или провайдер неактивны"
        }

    # Мержим default_params модели с переданными kwargs
    params = {}
    if model.default_params:
        try:
            params = json.loads(model.default_params)
        except json.JSONDecodeError:
            pass
    params.update(kwargs)

    # Создаём провайдер
    try:
        provider = AIProviderFactory.create_from_db_provider(model.provider)
    except AIProviderError as e:
        return {
            "success": False,
            "content": None,
            "model": model.api_identifier,
            "usage": {},
            "error": str(e)
        }

    # Отправляем запрос
    result = provider.send_message(model.api_identifier, messages, **params)

    # Если ошибка и есть fallback - пробуем fallback
    if not result["success"] and use_fallback:
        # Ищем fallback в stage_assignments
        from app.models import StageAssignment

        assignment = StageAssignment.query.filter_by(
            model_id=model_id,
            is_active=True
        ).first()

        if assignment and assignment.fallback_model_id:
            fallback_result = send_ai_request(
                model_id=assignment.fallback_model_id,
                messages=messages,
                use_fallback=False,  # Не используем вложенный fallback
                **kwargs
            )

            if fallback_result["success"]:
                fallback_result["fallback_used"] = True
                fallback_result["original_error"] = result["error"]
                return fallback_result

    return result
