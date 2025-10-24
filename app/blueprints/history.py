from flask import Blueprint, render_template
from flask_login import login_required
history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
@login_required
def index():
    return render_template('history/index.html', title='История обработок')
