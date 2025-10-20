from flask import Blueprint, render_template

history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
def index():
    return render_template('history/index.html', title='История обработок')
