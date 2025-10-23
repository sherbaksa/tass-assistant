# /home/mzeus2008/apps/tass_assistant/wsgi.py (фрагмент в начале)
import os
import sys
from pathlib import Path
PROJECT_HOME = '/home/mzeus2008/apps/tass_assistant'
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

def load_env_file(path: str):
    p = Path(path).expanduser()
    log_path = Path("/home/mzeus2008/.env_loader.log")
    try:
        if not p.exists():
            log_path.write_text(f"load_env_file: {p} does not exist\n")
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
        log_path.write_text("load_env_file: loaded variables: " + ",".join(vars_found) + "\n")
    except Exception as e:
        log_path.write_text("load_env_file: exception:\n" + repr(e) + "\n")

# вызов загрузки
load_env_file("~/.env_secrets")
# ВАЖНО: импортируем из вашего пакета "app"
from app.app import create_app
app = create_app()

# Для совместимости с WSGI
application = app

if __name__ == "__main__":
    app.run(debug=True)
