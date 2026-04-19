from flask import Blueprint

bp = Blueprint('models', __name__, template_folder='../templates')

from web.models import routes
