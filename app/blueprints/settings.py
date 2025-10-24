from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.auth.decorators import admin_required
from app.extensions import db
from app.models import User

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/')
@login_required
def index():
    return render_template('settings/index.html', title='Настройки')


@settings_bp.route('/users')
@login_required
@admin_required
def users():
    """Управление пользователями (только для админов)"""
    all_users = User.query.order_by(User.id).all()
    return render_template('settings/users.html', title='Управление пользователями', users=all_users)


@settings_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Переключить статус администратора у пользователя"""
    user = User.query.get_or_404(user_id)

    # Нельзя снять права у самого себя
    if user.id == current_user.id:
        flash("Вы не можете изменить свои собственные права администратора", "warning")
        return redirect(url_for('settings.users'))

    user.is_admin = not user.is_admin
    db.session.commit()

    action = "назначен администратором" if user.is_admin else "лишён прав администратора"
    flash(f"Пользователь {user.email} {action}", "success")
    return redirect(url_for('settings.users'))


@settings_bp.route('/registration/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_registration():
    """Включить/выключить регистрацию"""
    from flask import current_app
    current_enabled = current_app.config.get('REGISTRATION_ENABLED', True)

    # В текущей сессии меняем значение
    current_app.config['REGISTRATION_ENABLED'] = not current_enabled

    status = "включена" if not current_enabled else "отключена"
    flash(f"Регистрация новых пользователей {status}", "success")

    return redirect(url_for('settings.users'))