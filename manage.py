# manage.py
import click
from flask import Flask
from app.app import create_app
from app.extensions import db, mail
from app.models import User, Provider, AIModel, Stage
from app.auth.services import hash_password
from flask_mail import Message

app: Flask = create_app()


@app.cli.command("mail-dump-config")
def mail_dump_config():
    """Показать актуальные MAIL_* настройки, которые видит Flask."""
    keys = [
        "MAIL_SERVER", "MAIL_PORT", "MAIL_USE_TLS", "MAIL_USE_SSL",
        "MAIL_USERNAME", "MAIL_DEFAULT_SENDER"
    ]
    for k in keys:
        v = app.config.get(k)
        if k in ("MAIL_USERNAME",):
            shown = f"{v}" if v else None
        else:
            shown = v
        click.echo(f"{k} = {shown!r}")


@app.cli.command("smtp-login-test")
@click.option("--ssl", is_flag=True, help="Использовать SMTP_SSL (обычно порт 465)")
@click.option("--tls", is_flag=True, help="Использовать STARTTLS (обычно порт 587)")
def smtp_login_test(ssl, tls):
    """Прямой тест SMTP-логина. Не шлёт письмо, только EHLO/LOGIN/QUIT."""
    import smtplib
    server = app.config["MAIL_SERVER"]
    port = app.config["MAIL_PORT"]
    username = app.config["MAIL_USERNAME"]
    password = app.config["MAIL_PASSWORD"]

    click.echo(f"Connecting to {server}:{port} ssl={ssl} tls={tls}")
    try:
        if ssl:
            smtp = smtplib.SMTP_SSL(server, int(port), timeout=20)
            smtp.ehlo()
        else:
            smtp = smtplib.SMTP(server, int(port), timeout=20)
            smtp.ehlo()
            if tls:
                smtp.starttls()
                smtp.ehlo()

        click.echo("Attempting LOGIN ...")
        smtp.login(username, password)
        click.echo("LOGIN OK ✅")
        smtp.quit()
    except Exception as e:
        click.echo(f"LOGIN FAILED ❌: {e}")
        raise


@app.cli.command("create-user")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--active/--inactive", default=True, help="Сразу активировать (подтверждён email)")
@click.option("--staff/--no-staff", default=False, help="Сделать админом")
def create_user(email, password, active, staff):
    """Создать пользователя вручную (обходит подтверждение e-mail)."""
    with app.app_context():
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            click.echo("Пользователь уже существует")
            return
        u = User(
            email=email,
            password_hash=hash_password(password),
            is_active=active,
            is_staff=staff,
        )
        db.session.add(u)
        db.session.commit()
        click.echo(f"Создан пользователь: {email} (active={active}, staff={staff})")


@app.cli.command("promote-admin")
@click.option("--email", prompt=True)
def promote_admin(email):
    """Выдать флаг is_staff существующему пользователю."""
    with app.app_context():
        u = User.query.filter_by(email=email.strip().lower()).first()
        if not u:
            click.echo("Пользователь не найден")
            return
        u.is_staff = True
        db.session.commit()
        click.echo(f"{u.email} теперь администратор (is_staff=True)")


@app.cli.command("send-test-mail")
@click.option("--to", "to_addr", prompt=True, help="Куда отправить тестовое письмо")
def send_test_mail(to_addr):
    """Отправить тестовое письмо (проверка SMTP-настроек)."""
    with app.app_context():
        msg = Message(
            subject="Тестовое письмо — ТАСС ассистент",
            recipients=[to_addr],
            html="<p>Если вы это видите — SMTP работает ✅</p>",
        )
        mail.send(msg)
        click.echo(f"Отправлено на {to_addr}")


@app.cli.command("init-assistants")
def init_assistants():
    """Инициализировать базовые данные для системы ассистентов."""
    with app.app_context():
        click.echo("Инициализация системы ассистентов...")

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
                click.echo(f"  ✅ Создан этап: {stage_data['display_name']}")
            else:
                click.echo(f"  ⏭️  Этап уже существует: {stage_data['display_name']}")

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
                click.echo(f"  ✅ Создан провайдер: {prov_data['display_name']}")
            else:
                click.echo(f"  ⏭️  Провайдер уже существует: {prov_data['display_name']}")

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
                click.echo(f"  ⚠️  Провайдер {model_data['provider']} не найден для модели {model_data['name']}")
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
                click.echo(f"  ✅ Создана модель: {model_data['display_name']}")
            else:
                click.echo(f"  ⏭️  Модель уже существует: {model_data['display_name']}")

        db.session.commit()

        click.echo("\n✨ Инициализация завершена!")
        click.echo("\nСледующие шаги:")
        click.echo("1. Перейдите в Настройки → Ассистенты")
        click.echo("2. Добавьте API ключи для провайдеров")
        click.echo("3. Назначьте модели на этапы обработки")


if __name__ == "__main__":
    app.run()