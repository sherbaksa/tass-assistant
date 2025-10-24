from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(UserMixin, TimestampMixin, db.Model):
    """
    Модель пользователя.
    Важно: __str__ возвращает email, чтобы в шаблонах {{ current_user }} выводился человекочитаемо.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))

    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)

    def get_id(self) -> str:
        return str(self.id)

    # --- Человекочитаемое представление ---
    def __str__(self) -> str:
        # Это позволит в base.html писать: "Вы вошли как {{ current_user }}"
        # и видеть e-mail вместо длинной служебной строки.
        return self.email

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} active={self.is_active} staff={self.is_staff} admin={self.is_admin}>"

class EmailToken(TimestampMixin, db.Model):
    __tablename__ = "email_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.String(16), nullable=False)  # 'confirm' | 'reset'
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)

    user = db.relationship("User", backref=db.backref("email_tokens", lazy="dynamic"))

class AuditLog(TimestampMixin, db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    event = db.Column(db.String(64), nullable=False)  # LOGIN_SUCCESS, LOGIN_FAIL, PASSWORD_RESET_REQUEST, ...
    ip = db.Column(db.String(45))
    ua = db.Column(db.String(255))
    details = db.Column(db.Text)

    user = db.relationship("User", backref=db.backref("audit_events", lazy="dynamic"))
