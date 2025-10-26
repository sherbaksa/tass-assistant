from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
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


@settings_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_active(user_id):
    """Активировать/деактивировать пользователя (только для админов)"""
    user = User.query.get_or_404(user_id)

    # Нельзя деактивировать самого себя
    if user.id == current_user.id:
        flash("Вы не можете изменить свой собственный статус активности", "warning")
        return redirect(url_for('settings.users'))

    user.is_active = not user.is_active
    db.session.commit()

    action = "активирован" if user.is_active else "деактивирован"
    flash(f"Пользователь {user.email} {action}.", "success")
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


# ============================================================================
# Управление системными промптами (только для админов)
# ============================================================================

@settings_bp.route('/prompts')
@login_required
@admin_required
def prompts():
    """Управление системными промптами"""
    from app.models import Stage, SystemPrompt

    stages = Stage.query.order_by(Stage.order).all()

    # Получаем системные промпты для всех этапов
    prompts_dict = {}
    for stage in stages:
        system_prompt = SystemPrompt.query.filter_by(stage_id=stage.id).first()
        prompts_dict[stage.id] = system_prompt

    return render_template('settings/prompts.html',
                           title='Системные промпты',
                           stages=stages,
                           prompts=prompts_dict)


@settings_bp.route('/prompts/<int:stage_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_prompt(stage_id):
    """Редактирование системного промпта для этапа"""
    from app.models import Stage, SystemPrompt
    from app.services.prompt_manager import PromptManager

    stage = Stage.query.get_or_404(stage_id)
    system_prompt = SystemPrompt.query.filter_by(stage_id=stage_id).first()

    if request.method == 'POST':
        prompt_text = request.form.get('prompt_text', '').strip()
        description = request.form.get('description', '').strip()

        if not prompt_text:
            flash("Текст промпта не может быть пустым", "error")
            return redirect(url_for('settings.edit_prompt', stage_id=stage_id))

        # Обновляем или создаём системный промпт
        PromptManager.update_system_prompt(
            stage_id=stage_id,
            prompt_text=prompt_text,
            description=description if description else None
        )

        flash(f"Системный промпт для этапа '{stage.display_name}' обновлён", "success")
        return redirect(url_for('settings.prompts'))

    # GET - показываем форму
    return render_template('settings/edit_prompt.html',
                           title=f'Редактирование промпта: {stage.display_name}',
                           stage=stage,
                           system_prompt=system_prompt)


@settings_bp.route('/my-prompts')
@login_required
def my_prompts():
    """Управление личными промптами пользователя"""
    from app.models import Stage
    from app.services.prompt_manager import PromptManager

    stages = Stage.query.filter_by(is_active=True).order_by(Stage.order).all()

    # Получаем пользовательские промпты
    user_prompts_dict = {}
    for stage in stages:
        user_prompt = PromptManager.get_or_create_user_prompt(current_user.id, stage.id)
        user_prompts_dict[stage.id] = user_prompt

    return render_template('settings/my_prompts.html',
                           title='Мои промпты',
                           stages=stages,
                           prompts=user_prompts_dict)


@settings_bp.route('/my-prompts/<int:stage_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_my_prompt(stage_id):
    """Редактирование личного промпта пользователя"""
    from app.models import Stage
    from app.services.prompt_manager import PromptManager

    stage = Stage.query.get_or_404(stage_id)
    user_prompt = PromptManager.get_or_create_user_prompt(current_user.id, stage_id)

    if request.method == 'POST':
        prompt_text = request.form.get('prompt_text', '').strip()

        if not prompt_text:
            flash("Текст промпта не может быть пустым", "error")
            return redirect(url_for('settings.edit_my_prompt', stage_id=stage_id))

        # Обновляем пользовательский промпт
        PromptManager.update_user_prompt(
            user_id=current_user.id,
            stage_id=stage_id,
            prompt_text=prompt_text
        )

        flash(f"Ваш промпт для этапа '{stage.display_name}' обновлён", "success")
        return redirect(url_for('settings.my_prompts'))

    # GET - показываем форму
    return render_template('settings/edit_my_prompt.html',
                           title=f'Редактирование промпта: {stage.display_name}',
                           stage=stage,
                           user_prompt=user_prompt)


@settings_bp.route('/my-prompts/<int:stage_id>/reset', methods=['POST'])
@login_required
def reset_my_prompt(stage_id):
    """Сброс личного промпта к системному"""
    from app.models import Stage
    from app.services.prompt_manager import PromptManager

    stage = Stage.query.get_or_404(stage_id)

    try:
        PromptManager.reset_user_prompt(current_user.id, stage_id)
        flash(f"Промпт для этапа '{stage.display_name}' сброшен к системному", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for('settings.my_prompts'))


# ============================================================================
# Управление настройками поиска (Brave Search API)
# ============================================================================

@settings_bp.route('/search')
@login_required
@admin_required
def search_settings():
    """Настройки поисковой системы"""
    from flask import current_app

    # Получаем текущие настройки
    api_key = current_app.config.get('BRAVE_SEARCH_API_KEY', '')
    is_enabled = current_app.config.get('BRAVE_SEARCH_ENABLED', False)

    return render_template('settings/search.html',
                           title='Настройки поиска',
                           api_key=api_key,
                           is_enabled=is_enabled)


@settings_bp.route('/search/update', methods=['POST'])
@login_required
@admin_required
def update_search_settings():
    """Обновить настройки Brave Search API"""
    from flask import current_app
    import os

    api_key = request.form.get('api_key', '').strip()
    is_enabled = request.form.get('is_enabled') == 'on'

    # Обновляем в текущем конфиге
    current_app.config['BRAVE_SEARCH_API_KEY'] = api_key
    current_app.config['BRAVE_SEARCH_ENABLED'] = is_enabled

    # TODO: В будущем сохранять в БД или .env файл
    # Пока просто обновляем в памяти приложения

    if api_key:
        flash("Настройки Brave Search обновлены. Для постоянного сохранения добавьте в .env файл", "success")
    else:
        flash("API ключ удалён из конфигурации", "warning")

    return redirect(url_for('settings.search_settings'))


@settings_bp.route('/search/test', methods=['POST'])
@login_required
@admin_required
def test_search():
    """Тестирование подключения к Brave Search API"""
    from flask import current_app
    from app.services.search_providers import test_brave_connection

    api_key = request.form.get('api_key', '').strip()

    if not api_key:
        api_key = current_app.config.get('BRAVE_SEARCH_API_KEY')

    if not api_key:
        return jsonify({
            'success': False,
            'message': '❌ API ключ не указан'
        })

    # Тестируем подключение
    success, message = test_brave_connection(api_key)

    return jsonify({
        'success': success,
        'message': message
    })