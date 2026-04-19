from flask import Flask, redirect, url_for
import os
from web.extensions import login_manager, csrf
from web.config import config
from web.storage import init_storage


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 初始化存储（如果尚未初始化）
    from web.storage import storage as current_storage
    if current_storage is None:
        init_storage(app.config['STORAGE_FOLDER'])
    
    # 注册蓝图
    from web.auth import bp as auth_bp
    from web.dashboard import bp as dashboard_bp
    from web.tasks import bp as tasks_bp
    from web.models import bp as models_bp
    from web.data import bp as data_bp
    from web.api import bp as api_bp
    from web.projects import bp as projects_bp
    from web.workspace import bp as workspace_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(models_bp, url_prefix='/models')
    app.register_blueprint(data_bp, url_prefix='/data')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(workspace_bp, url_prefix='/workspace')
    
    # 创建上传目录
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)
    
    # 添加根路由
    @app.route('/')
    def index():
        """根路由 - 重定向到仪表板或登录页面"""
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('auth.login'))
    
    # 添加自定义过滤器
    @app.template_filter('format_datetime')
    def format_datetime_filter(value):
        """格式化日期时间字符串"""
        if not value:
            return '未知'
        try:
            # 处理 ISO 格式：2026-04-16T17:19:24.838696
            if 'T' in value:
                return value.split('T')[0]
            # 处理其他格式，尝试截取前 10 位
            if len(value) >= 10:
                return value[:10]
            return value
        except:
            return '未知'
    
    # 添加 context processor 注入项目信息
    @app.context_processor
    def inject_projects():
        """在所有模板中注入项目信息"""
        from web.projects import Project
        return {
            'projects': Project.get_all(),
            'current_project': None
        }
    
    return app
