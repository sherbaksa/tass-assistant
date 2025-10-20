from flask import Blueprint, render_template

assistants_bp = Blueprint('assistants', __name__, url_prefix='/assistants')

@assistants_bp.route('/')
def index():
    return render_template('assistants/index.html', title='Помощники обработки')
