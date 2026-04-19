from flask import Blueprint

bp = Blueprint('workspace', __name__, template_folder='../templates')

# Import routes at the end
from web.workspace import routes
