from datetime import datetime, timedelta
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from argon2 import PasswordHasher
from app.extensions import db, mail
from app.models import User, EmailToken, AuditLog
from flask_mail import Message

ph = PasswordHasher()

def hash_password(plain: str) -> str:
    return ph.hash(plain)

def verify_password(pw_hash: str, candidate: str) -> bool:
    try:
        return ph.verify(pw_hash, candidate)
    except Exception:
        return False

def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=current_app.config["SECRET_KEY"],
        salt=current_app.config.get("SECURITY_PASSWORD_SALT", "dev-salt"),
    )

def create_email_token(user: User, kind: str, hours: int) -> EmailToken:
    assert kind in ("confirm", "reset")
    s = _serializer()
    token = s.dumps({"uid": user.id, "type": kind})
    et = EmailToken(
        user_id=user.id,
        type=kind,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=hours),
    )
    db.session.add(et)
    db.session.commit()
    return et

def verify_email_token(token: str, max_age_seconds: int):
    s = _serializer()
    try:
        data = s.loads(token, max_age=max_age_seconds)
        return data
    except SignatureExpired:
        return None
    except BadSignature:
        return None

def send_email(subject: str, recipients: list[str], html: str) -> None:
    backend = (current_app.config.get("MAIL_BACKEND") or "smtp").lower()

    # ✅ Отправка через SendGrid API (HTTPS)
    if backend == "sendgrid":
        import requests

        api_key = current_app.config.get("SENDGRID_API_KEY")
        sender = current_app.config.get("MAIL_DEFAULT_SENDER")

        if not api_key or not sender:
            raise RuntimeError("SENDGRID_API_KEY or MAIL_DEFAULT_SENDER not set")

        url = "https://api.sendgrid.com/v3/mail/send"
        data = {
            "personalizations": [{"to": [{"email": r} for r in recipients]}],
            "from": {"email": sender},
            "subject": subject,
            "content": [{"type": "text/html", "value": html}],
        }

        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=data,
            timeout=15,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"SendGrid error {resp.status_code}: {resp.text}")
        return

    # ✅ fallback для локальной SMTP
    msg = Message(subject=subject, recipients=recipients, html=html)
    mail.send(msg)

def log_event(event: str, user_id: int | None, ip: str | None, ua: str | None, details: str | None = None):
    log = AuditLog(event=event, user_id=user_id, ip=ip, ua=ua, details=details)
    db.session.add(log)
    db.session.commit()
