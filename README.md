# News Editor Assistant

**News Editor Assistant** — веб-приложение для автоматизированного анализа новостных материалов с использованием AI-моделей от различных провайдеров (OpenAI, Google AI, Anthropic).

## Описание

Приложение помогает выпускающим редакторам информационных агентств анализировать входящие новости через многоэтапный pipeline обработки:

1. **Классификация** — определение категории новости для правильного размещения в новостной ленте
2. **Проверка на свежесть** — генерация поискового запроса для анализа публикаций в информационном поле
3. **Анализ свежести** — поиск через Brave Search и оценка актуальности материала
4. **Глубокий анализ** — проверка новости согласно редакционным стандартам агентства
5. **Рекомендации** — формирование рекомендаций для редактора на основе проведённого анализа

Для каждого этапа можно назначить основную AI-модель и резервную (fallback), выбрав из доступных провайдеров.

## Основные возможности

- Поддержка множественных AI-провайдеров (OpenAI, Google AI, Anthropic)
- Гибкая система назначения моделей на этапы обработки с fallback-механизмом
- Интеграция с Brave Search для проверки актуальности новостей
- Система аутентификации с подтверждением email
- Настраиваемые системные и пользовательские промпты для каждого этапа
- История обработки новостей
- Административная панель для управления пользователями, моделями и настройками

## Технический стек

- **Backend**: Flask 3.0.3
- **Database**: SQLAlchemy 2.0 (SQLite по умолчанию)
- **Authentication**: Flask-Login, argon2-cffi
- **Email**: Flask-Mail / SendGrid
- **Migrations**: Flask-Migrate (Alembic)
- **AI Providers**: OpenAI API, Google Gemini API, Anthropic Claude API
- **Search**: Brave Search API

## Требования

- Python 3.13+ (разработка велась на Python 3.13)
- pip или poetry для установки зависимостей
- SMTP-сервер или SendGrid API для отправки email
- API ключи от AI-провайдеров (минимум один)
- (Опционально) Brave Search API ключ для проверки свежести новостей

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/sherbaksa/tass-assistant.git
cd tass-assistant
```

### 2. Создание виртуального окружения

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Основные настройки Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_DEBUG=1

# База данных (по умолчанию SQLite)
# DATABASE_URL=sqlite:///app.db  # используется по умолчанию, можно не указывать

# Настройки безопасности
SECURITY_PASSWORD_SALT=your-password-salt-here

# Настройки регистрации
REGISTRATION_ENABLED=1  # 1 - включена, 0 - выключена

# Настройки cookies (для production установите SESSION_COOKIE_SECURE=1)
SESSION_COOKIE_SECURE=0  # для development=0, для production=1

# ===== НАСТРОЙКИ EMAIL =====
# Выберите один из вариантов ниже

# Вариант 1: SMTP (например, Mail.ru, Gmail, Yandex)
MAIL_BACKEND=smtp
MAIL_SERVER=smtp.mail.ru
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_USERNAME=your-email@mail.ru
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@mail.ru

# Вариант 2: SendGrid (для PythonAnywhere или если нет доступа к SMTP)
# MAIL_BACKEND=sendgrid
# SENDGRID_API_KEY=your-sendgrid-api-key
# MAIL_DEFAULT_SENDER=your-email@domain.com

# ===== BRAVE SEARCH (опционально) =====
# Если не указать, этап проверки свежести будет работать без реального поиска
BRAVE_SEARCH_API_KEY=your-brave-search-api-key
BRAVE_SEARCH_ENABLED=1  # 1 - включен, 0 - выключен
```

#### Получение API ключей и паролей приложений

**Для SMTP (Mail.ru, Gmail и т.д.):**
- Mail.ru: Настройки → Пароль и безопасность → Пароли для внешних приложений
- Gmail: Аккаунт Google → Безопасность → Двухэтапная аутентификация → Пароли приложений
- Используйте именно пароль приложения, а не основной пароль аккаунта

**Для SendGrid:**
1. Зарегистрируйтесь на https://sendgrid.com
2. Settings → API Keys → Create API Key
3. Выберите "Full Access" или настройте права для Mail Send

**Для Brave Search:**
1. Зарегистрируйтесь на https://brave.com/search/api/
2. Получите API ключ (есть бесплатный тариф)

**Для AI провайдеров** (настраиваются позже через веб-интерфейс):
- OpenAI: https://platform.openai.com/api-keys
- Google AI: https://makersuite.google.com/app/apikey
- Anthropic: https://console.anthropic.com/settings/keys

### 5. Инициализация базы данных

```bash
# Применить миграции
flask db upgrade

# Инициализировать систему ассистентов (провайдеры, модели, этапы)
flask init-assistants
```

### 6. Инициализация промптов

```bash
python init_prompts.py
```

### 7. Создание первого пользователя (администратора)

```bash
# Запустите приложение
python wsgi.py
# или
flask run

# Откройте в браузере http://localhost:5000
# Перейдите на страницу регистрации
# Зарегистрируйте первого пользователя - он автоматически станет администратором
```

**Важно:** Первый зарегистрированный пользователь автоматически получает права администратора. После регистрации проверьте email для подтверждения аккаунта.

Если email не приходит, проверьте:
```bash
# Проверка настроек почты
flask mail-dump-config

# Тест SMTP-подключения (для SMTP)
flask smtp-login-test --tls

# Отправка тестового письма
flask send-test-mail --to your-email@example.com
```

Альтернативный способ создания администратора через CLI (обходит подтверждение email):
```bash
flask create-user --email admin@example.com --password YourPassword --active --staff
```

### 8. Настройка AI провайдеров

После входа в систему как администратор:

1. Перейдите в **Настройки → Ассистенты → Провайдеры**
2. Добавьте API ключи для нужных провайдеров:
   - **OpenAI**: API ключ с https://platform.openai.com/api-keys
   - **Google AI**: API ключ с https://makersuite.google.com/app/apikey
   - **Anthropic**: API ключ с https://console.anthropic.com/settings/keys
3. Активируйте провайдеров, нажав кнопку "Тест подключения" для проверки
4. Перейдите в **Настройки → Ассистенты → Этапы**
5. Назначьте модели на каждый этап обработки:
   - Выберите основную модель
   - (Опционально) Выберите fallback-модель на случай сбоя
6. Активируйте назначения

### 9. Готово!

Приложение готово к работе. Откройте главную страницу и загрузите новость для анализа.

## Команды управления

Приложение поддерживает следующие CLI-команды:

```bash
# Управление пользователями
flask create-user                    # Создать пользователя интерактивно
flask promote-admin --email user@example.com  # Сделать пользователя администратором

# Проверка email
flask mail-dump-config              # Показать настройки почты
flask smtp-login-test --tls         # Тест SMTP-подключения
flask send-test-mail --to email     # Отправить тестовое письмо

# Инициализация данных
flask init-assistants               # Инициализировать провайдеров, модели, этапы
python init_prompts.py              # Инициализировать системные промпты

# Миграции базы данных
flask db migrate -m "description"   # Создать миграцию
flask db upgrade                    # Применить миграции
flask db downgrade                  # Откатить миграцию
```

## Деплой на PythonAnywhere

### Подготовка проекта

1. Зарегистрируйтесь на https://www.pythonanywhere.com (бесплатный аккаунт подойдёт)
2. В Dashboard создайте новое Web App:
   - Python version: 3.10 (или новее, если доступно)
   - Framework: Manual configuration

### Загрузка кода

**Вариант 1: Через Git (рекомендуется)**

Откройте Bash console на PythonAnywhere:

```bash
cd ~
git clone https://github.com/sherbaksa/tass-assistant.git
cd tass-assistant
```

**Вариант 2: Загрузка файлов**

Используйте вкладку "Files" для загрузки файлов проекта.

### Настройка виртуального окружения

В Bash console:

```bash
cd ~/news-editor-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Настройка переменных окружения

Создайте файл `~/.env_secrets` (в домашней директории, не в проекте!):

```bash
nano ~/.env_secrets
```

Добавьте переменные окружения:

```bash
export FLASK_ENV=production
export SECRET_KEY=your-very-long-secret-key-change-this
export SECURITY_PASSWORD_SALT=your-salt-change-this
export SESSION_COOKIE_SECURE=1

# SendGrid для отправки email (на бесплатном PythonAnywhere SMTP может не работать)
export MAIL_BACKEND=sendgrid
export SENDGRID_API_KEY=your-sendgrid-api-key
export MAIL_DEFAULT_SENDER=your-email@domain.com

# Brave Search (опционально)
export BRAVE_SEARCH_API_KEY=your-brave-api-key
export BRAVE_SEARCH_ENABLED=1

# Регистрация (можно отключить после создания админа)
export REGISTRATION_ENABLED=1
```

Сохраните файл (Ctrl+O, Enter, Ctrl+X).

**Важно:** Файл `~/.env_secrets` должен быть в домашней директории (`/home/yourusername/`), а не в папке проекта! Этот файл автоматически загружается в `wsgi.py`.

### Настройка WSGI

1. Откройте вкладку **Web** в PythonAnywhere Dashboard
2. В разделе "Code" найдите "WSGI configuration file" и кликните на ссылку
3. **Удалите всё содержимое** файла
4. Вставьте следующий код (замените `yourusername` на ваше имя пользователя):

```python
import os
import sys
from pathlib import Path

# Настройки для PythonAnywhere
PROJECT_HOME = '/home/yourusername/tass-assistant'
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

# Функция загрузки переменных окружения
def load_env_file(path: str):
    """Загрузка переменных окружения из файла"""
    p = Path(path).expanduser()
    log_path = Path("/home/yourusername/.env_loader.log")

    try:
        if not p.exists():
            try:
                log_path.write_text(f"load_env_file: {p} does not exist\n")
            except:
                pass
            return

        vars_found = []
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            vars_found.append(k)
            if k not in os.environ:
                os.environ[k] = v

        try:
            log_path.write_text("load_env_file: loaded variables: " + ",".join(vars_found) + "\n")
        except:
            pass

    except Exception as e:
        try:
            log_path.write_text("load_env_file: exception:\n" + repr(e) + "\n")
        except:
            pass

# Загрузка переменных окружения
load_env_file("~/.env_secrets")

# Импорт приложения
from app.app import create_app

application = create_app()
```

5. Сохраните файл

### Инициализация базы данных

В Bash console:

```bash
cd ~/tass-assistant
source venv/bin/activate

# Применить миграции
flask db upgrade

# Инициализировать систему
flask init-assistants

# Инициализировать промпты
python init_prompts.py
```

### Настройка статических файлов

1. В Web-вкладке найдите раздел **Static files**
2. Добавьте маппинг:
   - URL: `/static/`
   - Directory: `/home/yourusername/tass-assistant/app/static/`

### Запуск приложения

1. В Web-вкладке нажмите зелёную кнопку **Reload**
2. Откройте ваш сайт: `https://yourusername.pythonanywhere.com`
3. Зарегистрируйте первого пользователя (он станет администратором)
4. Подтвердите email (проверьте папку "Спам")
5. Войдите и настройте AI провайдеров в разделе Настройки → Ассистенты

### Обновление кода из Git

Для обновления приложения при изменениях в репозитории:

```bash
cd ~/tass-assistant
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # если были изменения в зависимостях
flask db upgrade  # если были новые миграции
```

Затем в Web-вкладке нажмите **Reload**.

### Отключение регистрации (опционально)

После создания всех необходимых пользователей:

1. Отредактируйте `~/.env_secrets`:
   ```bash
   export REGISTRATION_ENABLED=0
   ```
2. Reload приложения в Web-вкладке

Новые пользователи могут быть добавлены администратором через CLI:
```bash
flask create-user --email newuser@example.com --password pass123 --active
```

### Логи и отладка

Логи приложения на PythonAnywhere доступны в:
- Web tab → Log files → Error log
- Web tab → Log files → Server log

Лог загрузки переменных окружения: `~/.env_loader.log`

## Структура проекта

```
tass-assistant/
├── app/
│   ├── auth/              # Модуль аутентификации
│   ├── blueprints/        # Основные модули приложения
│   ├── services/          # Бизнес-логика (AI, поиск, промпты)
│   ├── static/            # Статические файлы (CSS, JS)
│   ├── templates/         # HTML-шаблоны
│   ├── app.py            # Фабрика приложения
│   ├── config.py         # Конфигурация
│   ├── extensions.py     # Инициализация расширений Flask
│   └── models.py         # Модели базы данных
├── migrations/           # Миграции Alembic
├── init_db.py           # Скрипт инициализации БД
├── init_prompts.py      # Скрипт инициализации промптов
├── manage.py            # CLI-команды управления
├── requirements.txt     # Зависимости Python
├── wsgi.py             # Точка входа WSGI
└── .env                # Переменные окружения (не коммитится!)
```

## Безопасность

### Важные замечания

1. **Никогда не коммитьте файл `.env` в Git!** (добавлен в `.gitignore`)
2. **Используйте сильные SECRET_KEY и SECURITY_PASSWORD_SALT** в production
3. **Установите SESSION_COOKIE_SECURE=1** при использовании HTTPS
4. **Храните API ключи в безопасности** - не делитесь ими
5. **На PythonAnywhere храните секреты в `~/.env_secrets`**, а не в репозитории

### Генерация безопасных ключей

```python
import secrets
print(secrets.token_urlsafe(32))  # для SECRET_KEY
print(secrets.token_urlsafe(16))  # для SECURITY_PASSWORD_SALT
```

## Вклад в проект

Если вы хотите внести свой вклад:

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/AmazingFeature`)
3. Закоммитьте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## Лицензия

Без лицензии

## Контакты

sherbaksa@gmail.com

## FAQ

### Не приходят письма для подтверждения регистрации

1. Проверьте папку "Спам"
2. Проверьте настройки в `.env`:
   ```bash
   flask mail-dump-config
   ```
3. Протестируйте отправку:
   ```bash
   flask send-test-mail --to your-email@example.com
   ```
4. Для Gmail убедитесь, что используете "Пароль приложения", а не основной пароль
5. На PythonAnywhere используйте SendGrid вместо SMTP

### Этап проверки свежести не работает

- Убедитесь, что `BRAVE_SEARCH_API_KEY` настроен в `.env`
- Установите `BRAVE_SEARCH_ENABLED=1`
- Если ключ не указан, система будет работать, но результаты поиска будут генерироваться AI (не реальные)

### AI провайдер не отвечает

1. Проверьте API ключ в разделе Настройки → Ассистенты → Провайдеры
2. Нажмите "Тест подключения"
3. Убедитесь, что на балансе провайдера есть средства
4. Проверьте лимиты запросов API
5. Настройте fallback-модель для критичных этапов

### Как добавить новых пользователей после отключения регистрации?

```bash
flask create-user --email newuser@example.com --password securepass --active
```

### Как сделать пользователя администратором?

```bash
flask promote-admin --email user@example.com
```

---

**Приятной работы с News Editor Assistant!**