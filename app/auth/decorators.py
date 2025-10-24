from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def admin_required(f):
    """
    Декоратор для проверки прав администратора.
    Использовать ПОСЛЕ @login_required
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Необходима авторизация", "warning")
            return redirect(url_for("auth.login"))

        if not current_user.is_admin:
            flash("Доступ запрещен. Требуются права администратора.", "danger")
            abort(403)

        return f(*args, **kwargs)

    return decorated_function