from flask import Blueprint, render_template
from flask_login import login_required
from app.auth.decorators import admin_required

assistants_bp = Blueprint('assistants', __name__, url_prefix='/assistants')

@assistants_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('assistants/index.html', title='Помощники обработки')