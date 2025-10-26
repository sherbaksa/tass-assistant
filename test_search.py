#!/usr/bin/env python
"""
Тестирование поискового сервиса
"""
from app.services.search_providers import search_news, test_brave_connection

# Виртуальный API ключ для тестирования структуры
VIRTUAL_API_KEY = "BSA_test_virtual_key_12345"


def test_connection():
    """Тест подключения к Brave Search"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К BRAVE SEARCH API")
    print("=" * 60)

    success, message = test_brave_connection(VIRTUAL_API_KEY)
    print(f"\nРезультат: {message}")
    print("=" * 60)


def test_search():
    """Тест поискового запроса"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПОИСКОВОГО ЗАПРОСА")
    print("=" * 60)

    query = "новости России сегодня"
    print(f"\nЗапрос: {query}")

    result = search_news(
        query=query,
        provider="brave",
        api_key=VIRTUAL_API_KEY,
        count=5,
        country="ru",
        search_lang="ru"
    )

    print(f"\nУспех: {result['success']}")
    print(f"Найдено результатов: {result['total']}")

    if result['success']:
        print("\nРезультаты:")
        for i, item in enumerate(result['results'], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   Источник: {item['source']}")
            print(f"   Описание: {item['description'][:100]}...")
    else:
        print(f"\nОшибка: {result['error']}")

    print("\n" + "=" * 60)


def test_search_structure():
    """Тест структуры ответа (без реального API)"""
    print("\n" + "=" * 60)
    print("ТЕСТ СТРУКТУРЫ ОТВЕТА")
    print("=" * 60)

    # Эмулируем ошибку подключения (т.к. у нас виртуальный ключ)
    result = search_news(
        query="test query",
        provider="brave",
        api_key=VIRTUAL_API_KEY,
        count=3
    )

    print("\nПроверка структуры ответа:")
    print(f"✓ Поле 'success': {type(result.get('success')).__name__}")
    print(f"✓ Поле 'query': {type(result.get('query')).__name__}")
    print(f"✓ Поле 'results': {type(result.get('results')).__name__}")
    print(f"✓ Поле 'total': {type(result.get('total')).__name__}")
    print(f"✓ Поле 'error': {type(result.get('error')).__name__}")

    print(f"\nОжидаемая ошибка (виртуальный ключ): {result.get('error')}")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🔍 ТЕСТИРОВАНИЕ ПОИСКОВОГО СЕРВИСА")
    print("=" * 60)
    print("ВНИМАНИЕ: Используется виртуальный API ключ")
    print("Реальные запросы не будут работать до получения настоящего ключа")
    print("=" * 60)

    # Тест структуры
    test_search_structure()

    # Тест подключения (ожидается ошибка с виртуальным ключом)
    test_connection()

    print("\n✅ Тестирование завершено!")
    print("После получения реального API ключа:")
    print("1. Добавьте его в .env: BRAVE_SEARCH_API_KEY=ваш_ключ")
    print("2. Запустите: python test_search.py")