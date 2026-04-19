from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from web.auth import User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "请登录以访问此页面"
login_manager.login_message_category = "warning"

csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login 用户加载器"""
    return User.get(int(user_id))
