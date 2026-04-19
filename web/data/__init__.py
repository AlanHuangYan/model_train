from flask import Blueprint

bp = Blueprint('data', __name__, template_folder='../templates')

from web.data import routes
