# manage.py
import click
from flask import Flask
from app.app import create_app
from app.extensions import db, mail
from app.models import User
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
        if k in ("MAIL_USERNAME", ):
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

if __name__ == "__main__":
    app.run()
