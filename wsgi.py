# wsgi.py - кросс-платформенная версия
import os
import sys
from pathlib import Path

# Определяем, на какой платформе работаем
IS_PYTHONANYWHERE = os.environ.get('PYTHONANYWHERE_DOMAIN') is not None or sys.platform == 'linux'

if IS_PYTHONANYWHERE:
    # Настройки для PythonAnywhere (Linux)
    PROJECT_HOME = '/home/mzeus2008/apps/tass_assistant'
    if PROJECT_HOME not in sys.path:
        sys.path.insert(0, PROJECT_HOME)


def load_env_file(path: str):
    """Загрузка переменных окружения из файла (только для PythonAnywhere)"""
    # На Windows пропускаем эту функцию
    if not IS_PYTHONANYWHERE:
        return

    p = Path(path).expanduser()
    log_path = Path("/home/mzeus2008/.env_loader.log")

    try:
        if not p.exists():
            try:
                log_path.write_text(f"load_env_file: {p} does not exist\n")
            except:
                pass  # Игнорируем ошибки записи в лог
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
            pass  # Игнорируем ошибки записи в лог

    except Exception as e:
        try:
            log_path.write_text("load_env_file: exception:\n" + repr(e) + "\n")
        except:
            pass  # Игнорируем ошибки записи в лог


# Вызов загрузки (только на PythonAnywhere)
if IS_PYTHONANYWHERE:
    load_env_file("~/.env_secrets")

# Импорт приложения
from app.app import create_app

app = create_app()

# Для совместимости с WSGI
application = app

if __name__ == "__main__":
    app.run(debug=True)