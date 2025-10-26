"""
Сервис для работы с поисковыми провайдерами (Brave Search, Google, etc.)
"""
import requests
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod


class SearchProviderError(Exception):
    """Базовое исключение для ошибок поисковых провайдеров"""
    pass


# ============================================================================
# Абстрактный слой для работы с поисковыми провайдерами
# ============================================================================

class BaseSearchProvider(ABC):
    """
    Базовый абстрактный класс для всех поисковых провайдеров
    """

    def __init__(self, api_key: str, additional_config: Optional[Dict] = None):
        """
        Args:
            api_key: API ключ провайдера
            additional_config: Дополнительная конфигурация (dict)
        """
        self.api_key = api_key
        self.additional_config = additional_config or {}
        self.timeout = self.additional_config.get('timeout', 10)

    @abstractmethod
    def get_provider_name(self) -> str:
        """Возвращает имя провайдера"""
        pass

    @abstractmethod
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Выполнить поисковый запрос

        Args:
            query: Поисковый запрос
            **kwargs: Дополнительные параметры (count, freshness, etc.)

        Returns:
            Dict с результатами поиска в унифицированном формате:
            {
                "success": bool,
                "query": str,           # исходный запрос
                "results": [            # список результатов
                    {
                        "title": str,   # заголовок
                        "url": str,     # URL
                        "description": str,  # описание/snippet
                        "published": str,    # дата публикации (если доступна)
                        "source": str        # источник/домен
                    }
                ],
                "total": int,           # общее количество найденных результатов
                "error": str            # сообщение об ошибке (если success=False)
            }
        """
        pass

    def validate_config(self) -> Tuple[bool, str]:
        """
        Проверить корректность конфигурации

        Returns:
            (success: bool, message: str)
        """
        if not self.api_key:
            return False, "API ключ не указан"
        return True, "Конфигурация корректна"


class BraveSearchProvider(BaseSearchProvider):
    """
    Провайдер для Brave Search API
    Документация: https://api.search.brave.com/app/documentation/web-search/get-started
    """

    BASE_URL = "https://api.search.brave.com/res/v1"

    def get_provider_name(self) -> str:
        return "brave"

    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Выполнить поиск через Brave Search API

        Поддерживаемые параметры kwargs:
        - count: количество результатов (по умолчанию 10, макс 20)
        - freshness: 'pd' (past day), 'pw' (past week), 'pm' (past month), 'py' (past year)
        - country: код страны (например, 'ru', 'us')
        - search_lang: язык поиска (например, 'ru', 'en')
        """
        endpoint = f"{self.BASE_URL}/web/search"

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        # Параметры запроса
        params = {
            "q": query,
            "count": kwargs.get("count", 10),
        }

        # Дополнительные параметры
        if "freshness" in kwargs:
            params["freshness"] = kwargs["freshness"]
        if "country" in kwargs:
            params["country"] = kwargs["country"]
        if "search_lang" in kwargs:
            params["search_lang"] = kwargs["search_lang"]

        try:
            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()

                # Извлекаем результаты
                results = []
                web_results = data.get("web", {}).get("results", [])

                for item in web_results:
                    result = {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("description", ""),
                        "published": item.get("age", ""),  # Brave возвращает относительное время
                        "source": self._extract_domain(item.get("url", ""))
                    }
                    results.append(result)

                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "error": None
                }

            elif response.status_code == 401:
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "total": 0,
                    "error": "Неверный API ключ"
                }
            elif response.status_code == 429:
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "total": 0,
                    "error": "Превышен лимит запросов"
                }
            else:
                error_text = response.text[:200] if response.text else "Unknown error"
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "total": 0,
                    "error": f"Brave Search API Error {response.status_code}: {error_text}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total": 0,
                "error": "Превышено время ожидания ответа"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total": 0,
                "error": f"Ошибка подключения к {self.BASE_URL}"
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total": 0,
                "error": f"Неизвестная ошибка: {str(e)}"
            }

    def _extract_domain(self, url: str) -> str:
        """Извлечь домен из URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url


class SearchProviderFactory:
    """
    Фабрика для создания поисковых провайдеров
    """

    _providers = {
        'brave': BraveSearchProvider,
        # Здесь можно добавить другие провайдеры в будущем
        # 'google': GoogleSearchProvider,
        # 'bing': BingSearchProvider,
    }

    @classmethod
    def create_provider(cls,
                        provider_name: str,
                        api_key: str,
                        additional_config: Optional[Dict] = None) -> BaseSearchProvider:
        """
        Создать поисковый провайдер по имени

        Args:
            provider_name: Имя провайдера (brave, google, bing)
            api_key: API ключ
            additional_config: Дополнительная конфигурация

        Returns:
            Экземпляр провайдера

        Raises:
            SearchProviderError: Если провайдер не найден
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise SearchProviderError(f"Неизвестный поисковый провайдер: {provider_name}")

        provider_class = cls._providers[provider_name]
        return provider_class(api_key, additional_config)

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Получить список доступных провайдеров"""
        return list(cls._providers.keys())


# ============================================================================
# Высокоуровневые функции для работы с поиском
# ============================================================================

def test_brave_connection(api_key: str) -> Tuple[bool, str]:
    """
    Тестирование подключения к Brave Search API

    Args:
        api_key: API ключ

    Returns:
        (success: bool, message: str)
    """
    if not api_key:
        return False, "API ключ не указан"

    try:
        provider = BraveSearchProvider(api_key)
        # Делаем тестовый запрос
        result = provider.search("test", count=1)

        if result["success"]:
            return True, f"✅ Подключение успешно! Найдено результатов: {result['total']}"
        else:
            return False, f"❌ {result['error']}"

    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"


def search_news(query: str,
                provider: str = "brave",
                api_key: Optional[str] = None,
                **kwargs) -> Dict[str, Any]:
    """
    Универсальная функция поиска новостей

    Args:
        query: Поисковый запрос
        provider: Имя провайдера (по умолчанию "brave")
        api_key: API ключ (если не указан, берётся из конфига)
        **kwargs: Дополнительные параметры поиска

    Returns:
        Dict с результатами поиска
    """
    # Если API ключ не передан, пытаемся получить из конфига
    if not api_key:
        from flask import current_app
        if provider == "brave":
            api_key = current_app.config.get('BRAVE_SEARCH_API_KEY')

        if not api_key:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total": 0,
                "error": f"API ключ для провайдера {provider} не настроен"
            }

    try:
        search_provider = SearchProviderFactory.create_provider(provider, api_key)
        return search_provider.search(query, **kwargs)
    except SearchProviderError as e:
        return {
            "success": False,
            "query": query,
            "results": [],
            "total": 0,
            "error": str(e)
        }