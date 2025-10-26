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


# ============================================================================
# Модели для системы управления AI ассистентами
# ============================================================================

class Provider(TimestampMixin, db.Model):
    """
    Провайдер API (OpenAI, Google, Anthropic, etc.)
    """
    __tablename__ = "providers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # openai, google, anthropic
    display_name = db.Column(db.String(128), nullable=False)  # OpenAI, Google AI, Anthropic
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    api_key = db.Column(db.String(512))  # TODO: шифрование добавим позже
    additional_config = db.Column(db.Text)  # JSON для доп. параметров (organization_id, project_id, etc.)

    # Relationships
    models = db.relationship("AIModel", back_populates="provider", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Provider id={self.id} name={self.name!r} active={self.is_active}>"


class AIModel(TimestampMixin, db.Model):
    """
    Конкретная модель ИИ (gpt-4o, gemini-flash, claude-sonnet, etc.)
    """
    __tablename__ = "ai_models"
    __table_args__ = (
        db.UniqueConstraint('provider_id', 'name', name='uq_provider_model'),
    )

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("providers.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(128), nullable=False)  # gpt-4o, gemini-flash-2.0
    display_name = db.Column(db.String(128), nullable=False)  # GPT-4o, Gemini Flash 2.0
    api_identifier = db.Column(db.String(128), nullable=False)  # как модель называется в API
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    default_params = db.Column(db.Text)  # JSON: {temperature: 0.7, max_tokens: 1000, etc.}

    # Relationships
    provider = db.relationship("Provider", back_populates="models")
    stage_assignments = db.relationship("StageAssignment", foreign_keys="StageAssignment.model_id",
                                        back_populates="model", lazy="dynamic")
    fallback_assignments = db.relationship("StageAssignment", foreign_keys="StageAssignment.fallback_model_id",
                                           back_populates="fallback_model", lazy="dynamic")

    def __repr__(self):
        return f"<AIModel id={self.id} name={self.name!r} provider={self.provider.name if self.provider else None}>"


class Stage(TimestampMixin, db.Model):
    """
    Этап обработки новостей (классификация, проверка на свежесть, анализ, рекомендации)
    """
    __tablename__ = "stages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True,
                     nullable=False)  # classification, freshness_check, analysis, recommendations
    display_name = db.Column(db.String(128), nullable=False)  # Классификация, Проверка на свежесть
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False, default=0)  # порядок отображения
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    assignments = db.relationship("StageAssignment", back_populates="stage", lazy="dynamic",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stage id={self.id} name={self.name!r} order={self.order}>"


class StageAssignment(TimestampMixin, db.Model):
    """
    Назначение модели на этап обработки
    """
    __tablename__ = "stage_assignments"

    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stages.id", ondelete="CASCADE"), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=False)
    fallback_model_id = db.Column(db.Integer, db.ForeignKey("ai_models.id", ondelete="SET NULL"))  # резервная модель
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    priority = db.Column(db.Integer, nullable=False, default=0)  # на случай нескольких назначений

    # Relationships
    stage = db.relationship("Stage", back_populates="assignments")
    model = db.relationship("AIModel", foreign_keys=[model_id], back_populates="stage_assignments")
    fallback_model = db.relationship("AIModel", foreign_keys=[fallback_model_id], back_populates="fallback_assignments")

    def __repr__(self):
        return f"<StageAssignment stage={self.stage.name if self.stage else None} model={self.model.name if self.model else None}>"


# ============================================================================
# Модели для управления системными промптами
# ============================================================================

class SystemPrompt(TimestampMixin, db.Model):
    """
    Системные промпты для этапов обработки (настраиваются администратором)
    """
    __tablename__ = "system_prompts"

    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stages.id", ondelete="CASCADE"), nullable=False, unique=True)
    prompt_text = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)  # Описание назначения промпта

    # Relationships
    stage = db.relationship("Stage", backref=db.backref("system_prompt", uselist=False))

    def __repr__(self):
        return f"<SystemPrompt id={self.id} stage={self.stage.name if self.stage else None}>"


class UserPrompt(TimestampMixin, db.Model):
    """
    Пользовательские промпты (копируются из системных, могут быть изменены пользователем)
    """
    __tablename__ = "user_prompts"
    __table_args__ = (
        db.UniqueConstraint('user_id', 'stage_id', name='uq_user_stage_prompt'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey("stages.id", ondelete="CASCADE"), nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    is_customized = db.Column(db.Boolean, nullable=False, default=False)  # True если пользователь изменял

    # Relationships
    user = db.relationship("User", backref=db.backref("user_prompts", lazy="dynamic", cascade="all, delete-orphan"))
    stage = db.relationship("Stage", backref=db.backref("user_prompts", lazy="dynamic"))

    def __repr__(self):
        return f"<UserPrompt id={self.id} user_id={self.user_id} stage={self.stage.name if self.stage else None} customized={self.is_customized}>"
