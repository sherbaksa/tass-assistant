from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.auth.decorators import admin_required
from app.extensions import db
from app.models import Provider, AIModel, Stage, StageAssignment
from app.services.ai_providers import test_provider_connection

assistants_bp = Blueprint('assistants', __name__, url_prefix='/assistants')


@assistants_bp.route('/')
@login_required
@admin_required
def index():
    """Главная страница управления ассистентами"""
    providers = Provider.query.order_by(Provider.name).all()
    stages = Stage.query.order_by(Stage.order).all()
    return render_template('assistants/index.html',
                           title='Помощники обработки',
                           providers=providers,
                           stages=stages)


# ============================================================================
# Управление провайдерами
# ============================================================================

@assistants_bp.route('/providers')
@login_required
@admin_required
def providers():
    """Список провайдеров API"""
    all_providers = Provider.query.order_by(Provider.name).all()
    return render_template('assistants/providers.html',
                           title='Управление провайдерами',
                           providers=all_providers)


@assistants_bp.route('/providers/<int:provider_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_provider(provider_id):
    """Редактирование провайдера (добавление API ключа)"""
    import json
    provider = Provider.query.get_or_404(provider_id)

    if request.method == 'POST':
        api_key = request.form.get('api_key', '').strip()
        base_url = request.form.get('base_url', '').strip()
        additional_config = request.form.get('additional_config', '').strip()
        is_active = request.form.get('is_active') == 'on'

        provider.api_key = api_key if api_key else None
        provider.is_active = is_active

        # Обработка конфигурации: base_url + additional_config
        config = {}
        if additional_config:
            try:
                config = json.loads(additional_config)
            except json.JSONDecodeError:
                flash("Неверный формат JSON в дополнительной конфигурации", "error")
                return redirect(url_for('assistants.edit_provider', provider_id=provider_id))

        # Добавляем base_url в конфиг, если указан
        if base_url:
            config['base_url'] = base_url

        provider.additional_config = json.dumps(config) if config else None

        db.session.commit()
        flash(f"Провайдер {provider.display_name} обновлен", "success")
        return redirect(url_for('assistants.providers'))

    # GET - извлекаем base_url из конфигурации
    base_url = ''
    if provider.additional_config:
        try:
            config = json.loads(provider.additional_config)
            base_url = config.get('base_url', '')
        except json.JSONDecodeError:
            pass

    return render_template('assistants/edit_provider.html',
                           title=f'Редактирование: {provider.display_name}',
                           provider=provider,
                           base_url=base_url)


@assistants_bp.route('/providers/<int:provider_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_provider(provider_id):
    """Включить/выключить провайдера"""
    provider = Provider.query.get_or_404(provider_id)
    provider.is_active = not provider.is_active
    db.session.commit()

    status = "активирован" if provider.is_active else "деактивирован"
    flash(f"Провайдер {provider.display_name} {status}", "success")
    return redirect(url_for('assistants.providers'))


@assistants_bp.route('/providers/<int:provider_id>/test', methods=['POST'])
@login_required
@admin_required
def test_provider(provider_id):
    """Тестирование подключения к провайдеру"""
    provider = Provider.query.get_or_404(provider_id)

    if not provider.api_key:
        return jsonify({
            'success': False,
            'message': '❌ API ключ не настроен'
        })

    # Тестируем подключение
    success, message = test_provider_connection(
        provider.name,
        provider.api_key,
        provider.additional_config
    )

    return jsonify({
        'success': success,
        'message': message
    })


# ============================================================================
# Управление моделями (CRUD)
# ============================================================================

@assistants_bp.route('/models')
@login_required
@admin_required
def models():
    """Список моделей AI с фильтром по активности"""
    show_inactive = request.args.get('show_inactive', '0') == '1'

    query = AIModel.query.join(Provider)
    if not show_inactive:
        query = query.filter(AIModel.is_active == True)

    all_models = query.order_by(Provider.name, AIModel.name).all()

    return render_template('assistants/models.html',
                           title='Управление моделями',
                           models=all_models,
                           show_inactive=show_inactive)


@assistants_bp.route('/models/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_model():
    """Создание новой модели"""
    if request.method == 'POST':
        provider_id = request.form.get('provider_id', type=int)
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        api_identifier = request.form.get('api_identifier', '').strip()
        default_params = request.form.get('default_params', '').strip()
        is_active = request.form.get('is_active') == 'on'

        # Валидация
        if not all([provider_id, name, display_name, api_identifier]):
            flash("Заполните все обязательные поля", "error")
            return redirect(url_for('assistants.create_model'))

        # Проверка на дубликат (provider_id + name должны быть уникальны)
        existing = AIModel.query.filter_by(provider_id=provider_id, name=name).first()
        if existing:
            flash(f"Модель с именем '{name}' у этого провайдера уже существует", "error")
            return redirect(url_for('assistants.create_model'))

        # Создание модели
        model = AIModel(
            provider_id=provider_id,
            name=name,
            display_name=display_name,
            api_identifier=api_identifier,
            default_params=default_params if default_params else None,
            is_active=is_active
        )
        db.session.add(model)
        db.session.commit()

        flash(f"Модель {display_name} создана", "success")
        return redirect(url_for('assistants.models'))

    # GET - показываем форму
    providers = Provider.query.order_by(Provider.display_name).all()
    return render_template('assistants/edit_model.html',
                           title='Добавить модель',
                           model=None,
                           providers=providers)


@assistants_bp.route('/models/<int:model_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_model(model_id):
    """Редактирование модели"""
    model = AIModel.query.get_or_404(model_id)

    if request.method == 'POST':
        provider_id = request.form.get('provider_id', type=int)
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        api_identifier = request.form.get('api_identifier', '').strip()
        default_params = request.form.get('default_params', '').strip()
        is_active = request.form.get('is_active') == 'on'

        # Валидация
        if not all([provider_id, name, display_name, api_identifier]):
            flash("Заполните все обязательные поля", "error")
            return redirect(url_for('assistants.edit_model', model_id=model_id))

        # Проверка на дубликат (кроме самой себя)
        existing = AIModel.query.filter(
            AIModel.provider_id == provider_id,
            AIModel.name == name,
            AIModel.id != model_id
        ).first()
        if existing:
            flash(f"Модель с именем '{name}' у этого провайдера уже существует", "error")
            return redirect(url_for('assistants.edit_model', model_id=model_id))

        # Обновление
        model.provider_id = provider_id
        model.name = name
        model.display_name = display_name
        model.api_identifier = api_identifier
        model.default_params = default_params if default_params else None
        model.is_active = is_active

        db.session.commit()
        flash(f"Модель {display_name} обновлена", "success")
        return redirect(url_for('assistants.models'))

    # GET - показываем форму
    providers = Provider.query.order_by(Provider.display_name).all()
    return render_template('assistants/edit_model.html',
                           title=f'Редактирование: {model.display_name}',
                           model=model,
                           providers=providers)


@assistants_bp.route('/models/<int:model_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_model(model_id):
    """Удаление модели"""
    model = AIModel.query.get_or_404(model_id)

    # Проверяем, не используется ли модель в активных назначениях
    active_assignments = StageAssignment.query.filter(
        db.or_(
            StageAssignment.model_id == model_id,
            StageAssignment.fallback_model_id == model_id
        ),
        StageAssignment.is_active == True
    ).count()

    if active_assignments > 0:
        flash(
            f"Невозможно удалить модель {model.display_name}: используется в {active_assignments} активных назначениях. Сначала удалите назначения.",
            "error")
        return redirect(url_for('assistants.models'))

    display_name = model.display_name
    db.session.delete(model)
    db.session.commit()

    flash(f"Модель {display_name} удалена", "success")
    return redirect(url_for('assistants.models'))


@assistants_bp.route('/models/<int:model_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_model(model_id):
    """Включить/выключить модель"""
    model = AIModel.query.get_or_404(model_id)
    model.is_active = not model.is_active
    db.session.commit()

    status = "активирована" if model.is_active else "деактивирована"
    flash(f"Модель {model.display_name} {status}", "success")
    return redirect(url_for('assistants.models'))


# ============================================================================
# Управление этапами и назначениями
# ============================================================================

@assistants_bp.route('/stages')
@login_required
@admin_required
def stages():
    """Управление этапами обработки и назначением моделей"""
    all_stages = Stage.query.order_by(Stage.order).all()
    active_models = AIModel.query.filter_by(is_active=True).join(Provider).filter(Provider.is_active == True).order_by(
        Provider.name, AIModel.name).all()

    # Получаем текущие назначения
    assignments = {}
    for stage in all_stages:
        active_assignment = StageAssignment.query.filter_by(stage_id=stage.id, is_active=True).first()
        assignments[stage.id] = active_assignment

    return render_template('assistants/stages.html',
                           title='Настройка этапов обработки',
                           stages=all_stages,
                           models=active_models,
                           assignments=assignments)


@assistants_bp.route('/stages/<int:stage_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_model(stage_id):
    """Назначить модель на этап"""
    stage = Stage.query.get_or_404(stage_id)
    model_id = request.form.get('model_id', type=int)
    fallback_model_id = request.form.get('fallback_model_id', type=int)

    if not model_id:
        flash("Выберите модель", "error")
        return redirect(url_for('assistants.stages'))

    model = AIModel.query.get_or_404(model_id)

    # Деактивируем предыдущие назначения для этого этапа
    StageAssignment.query.filter_by(stage_id=stage_id, is_active=True).update({'is_active': False})

    # Создаем новое назначение
    assignment = StageAssignment(
        stage_id=stage_id,
        model_id=model_id,
        fallback_model_id=fallback_model_id if fallback_model_id else None,
        is_active=True
    )
    db.session.add(assignment)
    db.session.commit()

    flash(f"Этап '{stage.display_name}' → {model.display_name}", "success")
    return redirect(url_for('assistants.stages'))


@assistants_bp.route('/stages/<int:stage_id>/unassign', methods=['POST'])
@login_required
@admin_required
def unassign_model(stage_id):
    """Убрать назначение с этапа"""
    StageAssignment.query.filter_by(stage_id=stage_id, is_active=True).update({'is_active': False})
    db.session.commit()

    stage = Stage.query.get_or_404(stage_id)
    flash(f"Назначение для этапа '{stage.display_name}' удалено", "success")
    return redirect(url_for('assistants.stages'))