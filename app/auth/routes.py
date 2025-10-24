from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.exceptions import NotFound
from app.auth import auth_bp
from app.auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.auth.services import (
    hash_password, verify_password, create_email_token, verify_email_token,
    send_email, log_event
)
from app.extensions import db, login_manager
from app.models import User, EmailToken

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Регистрация ---
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
        # Проверка, разрешена ли регистрация
        from flask import current_app
        if not current_app.config.get('REGISTRATION_ENABLED', True):
            flash("Регистрация новых пользователей временно отключена", "warning")
            return redirect(url_for("auth.login"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким e-mail уже существует", "danger")
            return render_template("auth/register.html", form=form)

        # Проверяем, есть ли уже пользователи в системе
        is_first_user = User.query.count() == 0

        user = User(
            email=email,
            password_hash=hash_password(form.password.data),
            is_active=False,
            is_admin=is_first_user  # Первый пользователь автоматически становится админом
        )
        db.session.add(user)
        db.session.commit()

        et = create_email_token(user, "confirm", hours=48)
        from app.auth.emails import render_confirm_email
        html = render_confirm_email(user, et.token)
        send_email("Подтвердите e-mail", [user.email], html)

        flash("Письмо с подтверждением отправлено.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)

# --- Подтверждение e-mail ---
@auth_bp.route("/confirm/<token>")
def confirm_email(token):
    data = verify_email_token(token, max_age_seconds=48*3600)
    if not data or data.get("type") != "confirm":
        flash("Ссылка недействительна или просрочена", "danger")
        return redirect(url_for("auth.login"))

    et = EmailToken.query.filter_by(token=token, type="confirm").first()
    if not et or et.used_at:
        flash("Ссылка уже использована", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(data["uid"])
    if not user:
        raise NotFound()

    user.is_active = True
    et.used_at = datetime.utcnow()
    db.session.commit()

    flash("E-mail подтверждён. Можете войти.", "success")
    return redirect(url_for("auth.login"))

# --- Логин ---
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Неверный e-mail или пароль", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("E-mail не подтверждён. Проверьте почту или запросите повторную отправку.", "warning")
            return render_template("auth/login.html", form=form)

        if not verify_password(user.password_hash, form.password.data):
            flash("Неверный e-mail или пароль", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user)
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = request.remote_addr
        db.session.commit()

        log_event("LOGIN_SUCCESS", user.id, request.remote_addr, request.headers.get("User-Agent"))
        flash("Добро пожаловать!", "success")
        next_url = request.args.get("next") or url_for("main.index")
        return redirect(next_url)

    return render_template("auth/login.html", form=form)

# --- Выход ---
@auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Вы вышли из системы.", "info")
    return redirect(url_for("main.index"))

# --- Сброс пароля: запрос письма ---
@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            et = create_email_token(user, "reset", hours=2)
            from app.auth.emails import render_reset_email
            html = render_reset_email(user, et.token)
            send_email("Сброс пароля", [user.email], html)
        flash("Если e-mail найден, мы отправили письмо со ссылкой для сброса.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)

# --- Сброс пароля: установка нового ---
@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    data = verify_email_token(token, max_age_seconds=2*3600)
    if not data or data.get("type") != "reset":
        flash("Ссылка недействительна или просрочена", "danger")
        return redirect(url_for("auth.login"))

    et = EmailToken.query.filter_by(token=token, type="reset").first()
    if not et or et.used_at:
        flash("Ссылка уже использована", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(data["uid"])
    if not user:
        raise NotFound()

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = hash_password(form.password.data)
        et.used_at = datetime.utcnow()
        db.session.commit()
        flash("Пароль обновлён. Войдите с новым паролем.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
