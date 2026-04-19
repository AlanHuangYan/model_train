# Web 管理界面实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个基于 Flask 的 Web 管理界面，支持用户认证、任务管理、模型管理、数据管理等功能。

**Architecture:** 采用 Flask 应用工厂模式和 Blueprints，前后端分离架构，使用 JSON 文件进行数据存储。

**Tech Stack:** Flask 3.1.2, Flask-Login, Flask-WTF, Bootstrap 5, Pandas, scikit-learn

---

## TODO 功能列表（后期实现）

在开始之前，先记录从参考项目中学到的好功能，标记为 TODO 供后期实现：

### 高优先级 TODO
- [ ] TODO: 模型预测功能 - 允许用户上传测试数据并进行预测
- [ ] TODO: 实验跟踪 - 记录每次训练的详细参数和结果，支持对比分析
- [ ] TODO: 数据可视化 - 上传数据后自动显示数据分布图、特征相关性热力图
- [ ] TODO: 模型注册表 - 为模型添加标签和描述，支持状态管理

### 中优先级 TODO
- [ ] TODO: 超参数调优 - 支持网格搜索和随机搜索
- [ ] TODO: 模型导出 - 导出模型为不同格式（ONNX、PMML 等）
- [ ] TODO: 高级监控 - 模型性能监控、数据漂移检测
- [ ] TODO: 报告生成 - 自动生成训练报告（PDF/HTML）

### 低优先级 TODO
- [ ] TODO: 用户协作功能 - 团队共享项目和模型，模型评论和批注
- [ ] TODO: 自动化功能 - 自动选择最佳模型、自动特征工程
- [ ] TODO: 训练任务通知 - 邮件/Webhook 通知

---

## 任务分解

### 任务 1: 项目结构搭建和依赖安装

**Files:**
- Create: `e:\Works\Projects\ai\model_train\web\__init__.py`
- Create: `e:\Works\Projects\ai\model_train\web\extensions.py`
- Create: `e:\Works\Projects\ai\model_train\web\config.py`
- Create: `e:\Works\Projects\ai\model_train\web\storage.py`
- Create: `e:\Works\Projects\ai\model_train\requirements-web.txt`
- Create: `e:\Works\Projects\ai\model_train\run.py`

- [ ] **Step 1: 创建 Web 依赖文件**

```txt
# Web 应用依赖
Flask==3.1.2
Flask-Login==0.6.3
Flask-WTF==1.2.2
Flask-SQLAlchemy==3.1.1
Werkzeug==3.1.5
python-dotenv==1.0.0

# 数据处理
pandas==2.0.3
scikit-learn==1.3.0
PyYAML==6.0.1

# 开发依赖
pytest==7.4.0
```

- [ ] **Step 2: 创建配置文件**

```python
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF token 永不过期（简化使用）
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 存储文件路径
    STORAGE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage')
    
    # 模型存储路径
    MODEL_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

- [ ] **Step 3: 创建扩展模块**

```python
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "请登录以访问此页面"
login_manager.login_message_category = "warning"

csrf = CSRFProtect()
```

- [ ] **Step 4: 创建存储管理模块**

```python
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class JSONStorage:
    """JSON 文件存储管理"""
    
    def __init__(self, storage_folder):
        self.storage_folder = storage_folder
        os.makedirs(storage_folder, exist_ok=True)
    
    def _get_file_path(self, collection):
        """获取集合文件路径"""
        return os.path.join(self.storage_folder, f"{collection}.json")
    
    def load(self, collection):
        """加载集合数据"""
        file_path = self._get_file_path(collection)
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save(self, collection, data):
        """保存集合数据"""
        file_path = self._get_file_path(collection)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def insert(self, collection, document):
        """插入文档"""
        data = self.load(collection)
        document['_id'] = len(data) + 1
        document['created_at'] = datetime.now().isoformat()
        data.append(document)
        self.save(collection, data)
        return document['_id']
    
    def find(self, collection, query=None):
        """查询文档"""
        data = self.load(collection)
        if query is None:
            return data
        
        # 简单查询支持
        results = []
        for doc in data:
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                results.append(doc)
        return results
    
    def update(self, collection, doc_id, updates):
        """更新文档"""
        data = self.load(collection)
        for doc in data:
            if doc.get('_id') == doc_id:
                doc.update(updates)
                doc['updated_at'] = datetime.now().isoformat()
                self.save(collection, data)
                return True
        return False
    
    def delete(self, collection, doc_id):
        """删除文档"""
        data = self.load(collection)
        data = [doc for doc in data if doc.get('_id') != doc_id]
        self.save(collection, data)
        return True


# 创建全局存储实例
storage = None


def init_storage(storage_folder):
    """初始化存储"""
    global storage
    storage = JSONStorage(storage_folder)
    return storage
```

- [ ] **Step 5: 创建应用工厂**

```python
from flask import Flask
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
    
    # 初始化存储
    init_storage(app.config['STORAGE_FOLDER'])
    
    # 注册蓝图
    from web.auth import bp as auth_bp
    from web.dashboard import bp as dashboard_bp
    from web.tasks import bp as tasks_bp
    from web.models import bp as models_bp
    from web.data import bp as data_bp
    from web.api import bp as api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(models_bp, url_prefix='/models')
    app.register_blueprint(data_bp, url_prefix='/data')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 创建上传目录
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)
    
    return app
```

- [ ] **Step 6: 创建应用入口**

```python
from web import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
```

- [ ] **Step 7: 提交代码**

```bash
git add requirements-web.txt web/__init__.py web/extensions.py web/config.py web/storage.py run.py
git commit -m "feat: Web 项目结构搭建"
```

### 任务 2: 用户认证系统实现

**Files:**
- Create: `e:\Works\Projects\ai\model_train\web\auth\__init__.py`
- Create: `e:\Works\Projects\ai\model_train\web\auth\routes.py`
- Create: `e:\Works\Projects\ai\model_train\web\auth\forms.py`
- Create: `e:\Works\Projects\ai\model_train\web\templates\auth\login.html`
- Create: `e:\Works\Projects\ai\model_train\web\templates\auth\register.html`

- [ ] **Step 1: 创建认证表单**

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from web.storage import storage


class LoginForm(FlaskForm):
    """登录表单"""
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    """注册表单"""
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(), EqualTo('password', message='两次密码必须一致')
    ])
    submit = SubmitField('注册')
    
    def validate_email(self, field):
        """验证邮箱是否已存在"""
        users = storage.find('users', {'email': field.data})
        if users:
            raise ValidationError('该邮箱已被注册')
```

- [ ] **Step 2: 创建用户模型类**

```python
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from web.storage import storage


class User(UserMixin):
    """用户模型"""
    
    def __init__(self, id, email, password_hash, is_admin=False):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get(user_id):
        """根据 ID 获取用户"""
        users = storage.find('users', {'_id': user_id})
        if not users:
            return None
        user_data = users[0]
        return User(
            id=user_data['_id'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            is_admin=user_data.get('is_admin', False)
        )
    
    @staticmethod
    def find_by_email(email):
        """根据邮箱查找用户"""
        users = storage.find('users', {'email': email})
        if not users:
            return None
        user_data = users[0]
        return User(
            id=user_data['_id'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            is_admin=user_data.get('is_admin', False)
        )
    
    @staticmethod
    def create(email, password, is_admin=False):
        """创建用户"""
        from web.storage import storage
        user_data = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_admin': is_admin,
            'active': True
        }
        storage.insert('users', user_data)
```

- [ ] **Step 3: 创建认证路由**

```python
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from web.auth.forms import LoginForm, RegistrationForm
from web.auth import User
from web.storage import storage

bp = Blueprint('auth', __name__, template_folder='templates')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        flash('邮箱或密码错误', 'danger')
    
    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        User.create(form.email.data, form.password.data)
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已登出', 'info')
    return redirect(url_for('auth.login'))
```

- [ ] **Step 4: 创建登录模板**

```html
{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0">用户登录</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    {{ form.hidden_tag() }}
                    
                    <div class="mb-3">
                        {{ form.email.label(class="form-label") }}
                        {{ form.email(class="form-control") }}
                        {% for error in form.email.errors %}
                        <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>
                    
                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control") }}
                        {% for error in form.password.errors %}
                        <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>
                    
                    <div class="mb-3 form-check">
                        {{ form.remember(class="form-check-input") }}
                        {{ form.remember.label(class="form-check-label") }}
                    </div>
                    
                    <div class="d-grid">
                        {{ form.submit(class="btn btn-primary") }}
                    </div>
                </form>
                
                <hr>
                
                <div class="text-center">
                    <a href="{{ url_for('auth.register') }}">没有账号？立即注册</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: 创建注册模板**

```html
{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0">用户注册</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    {{ form.hidden_tag() }}
                    
                    <div class="mb-3">
                        {{ form.email.label(class="form-label") }}
                        {{ form.email(class="form-control") }}
                        {% for error in form.email.errors %}
                        <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>
                    
                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control") }}
                        {% for error in form.password.errors %}
                        <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>
                    
                    <div class="mb-3">
                        {{ form.confirm_password.label(class="form-label") }}
                        {{ form.confirm_password(class="form-control") }}
                        {% for error in form.confirm_password.errors %}
                        <div class="text-danger">{{ error }}</div>
                        {% endfor %}
                    </div>
                    
                    <div class="d-grid">
                        {{ form.submit(class="btn btn-primary") }}
                    </div>
                </form>
                
                <hr>
                
                <div class="text-center">
                    <a href="{{ url_for('auth.login') }}">已有账号？立即登录</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 6: 更新扩展模块添加用户加载器**

```python
# 在 web/extensions.py 中添加
from web.auth import User

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login 用户加载器"""
    return User.get(int(user_id))
```

- [ ] **Step 7: 提交代码**

```bash
git add web/auth/__init__.py web/auth/routes.py web/auth/forms.py web/templates/auth/login.html web/templates/auth/register.html
git commit -m "feat: 用户认证系统实现"
```

### 任务 3: 基础模板和仪表板实现

**Files:**
- Create: `e:\Works\Projects\ai\model_train\web\templates\base.html`
- Create: `e:\Works\Projects\ai\model_train\web\dashboard\__init__.py`
- Create: `e:\Works\Projects\ai\model_train\web\dashboard\routes.py`
- Create: `e:\Works\Projects\ai\model_train\web\templates\dashboard\index.html`

- [ ] **Step 1: 创建基础模板**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}模型训练管理系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        .sidebar {
            min-height: 100vh;
            background-color: #343a40;
        }
        .sidebar a {
            color: #fff;
            text-decoration: none;
        }
        .sidebar a:hover {
            color: #adb5bd;
        }
        .content {
            padding: 20px;
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- 侧边栏 -->
            <nav class="col-md-3 col-lg-2 d-md-block sidebar p-3">
                <div class="text-center mb-4">
                    <h5 class="text-white">模型训练管理</h5>
                </div>
                
                {% if current_user.is_authenticated %}
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('dashboard.index') }}">
                            <i class="bi bi-speedometer2"></i> 仪表板
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('tasks.list_tasks') }}">
                            <i class="bi bi-list-task"></i> 任务管理
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('models.list_models') }}">
                            <i class="bi bi-robot"></i> 模型管理
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('data.list_data') }}">
                            <i class="bi bi-database"></i> 数据管理
                        </a>
                    </li>
                </ul>
                
                <hr class="bg-white">
                
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('auth.logout') }}">
                            <i class="bi bi-box-arrow-right"></i> 登出
                        </a>
                    </li>
                </ul>
                {% else %}
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('auth.login') }}">
                            <i class="bi bi-box-arrow-in-right"></i> 登录
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('auth.register') }}">
                            <i class="bi bi-person-plus"></i> 注册
                        </a>
                    </li>
                </ul>
                {% endif %}
            </nav>
            
            <!-- 主内容区 -->
            <main class="col-md-9 ms-sm-auto col-lg-10 content">
                <!-- 顶部导航 -->
                <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
                    <div class="container-fluid">
                        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                            <span class="navbar-toggler-icon"></span>
                        </button>
                        <div class="collapse navbar-collapse" id="navbarNav">
                            <ul class="navbar-nav me-auto">
                                <li class="nav-item">
                                    <span class="nav-link">欢迎，{{ current_user.email if current_user.is_authenticated else '访客' }}</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </nav>
                
                <!-- 闪络消息 -->
                {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                {% for category, message in messages %}
                <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
                {% endfor %}
                {% endif %}
                {% endwith %}
                
                <!-- 页面内容 -->
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: 创建仪表板路由**

```python
from flask import Blueprint, render_template
from flask_login import login_required
from web.storage import storage

bp = Blueprint('dashboard', __name__, template_folder='templates')


@bp.route('/')
@login_required
def index():
    """仪表板首页"""
    # 获取统计数据
    tasks = storage.load('tasks')
    models = storage.load('models')
    data_files = storage.load('data_files')
    
    # 统计信息
    stats = {
        'total_tasks': len(tasks),
        'pending_tasks': len([t for t in tasks if t.get('status') == 'pending']),
        'running_tasks': len([t for t in tasks if t.get('status') == 'running']),
        'completed_tasks': len([t for t in tasks if t.get('status') == 'completed']),
        'total_models': len(models),
        'total_data_files': len(data_files)
    }
    
    # 最近的任务
    recent_tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    return render_template('dashboard/index.html', stats=stats, recent_tasks=recent_tasks)
```

- [ ] **Step 3: 创建仪表板模板**

```html
{% extends "base.html" %}

{% block title %}仪表板 - 模型训练管理系统{% endblock %}

{% block content %}
<h2>仪表板</h2>

<!-- 统计卡片 -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <h5 class="card-title">总任务数</h5>
                <h2>{{ stats.total_tasks }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <h5 class="card-title">待处理任务</h5>
                <h2>{{ stats.pending_tasks }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <h5 class="card-title">运行中任务</h5>
                <h2>{{ stats.running_tasks }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <h5 class="card-title">已完成任务</h5>
                <h2>{{ stats.completed_tasks }}</h2>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">模型统计</h5>
            </div>
            <div class="card-body">
                <p>总模型数：<strong>{{ stats.total_models }}</strong></p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">数据统计</h5>
            </div>
            <div class="card-body">
                <p>数据文件数：<strong>{{ stats.total_data_files }}</strong></p>
            </div>
        </div>
    </div>
</div>

<!-- 最近任务 -->
<div class="card mt-4">
    <div class="card-header">
        <h5 class="mb-0">最近任务</h5>
    </div>
    <div class="card-body">
        {% if recent_tasks %}
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>名称</th>
                    <th>状态</th>
                    <th>创建时间</th>
                </tr>
            </thead>
            <tbody>
                {% for task in recent_tasks %}
                <tr>
                    <td>{{ task._id }}</td>
                    <td>{{ task.name }}</td>
                    <td>
                        {% if task.status == 'pending' %}
                        <span class="badge bg-warning">待处理</span>
                        {% elif task.status == 'running' %}
                        <span class="badge bg-info">运行中</span>
                        {% elif task.status == 'completed' %}
                        <span class="badge bg-success">已完成</span>
                        {% elif task.status == 'failed' %}
                        <span class="badge bg-danger">失败</span>
                        {% endif %}
                    </td>
                    <td>{{ task.created_at }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p class="text-muted">暂无任务</p>
        {% endif %}
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: 提交代码**

```bash
git add web/templates/base.html web/dashboard/__init__.py web/dashboard/routes.py web/templates/dashboard/index.html
git commit -m "feat: 基础模板和仪表板实现"
```

### 任务 4: 任务管理功能实现

**Files:**
- Create: `e:\Works\Projects\ai\model_train\web\tasks\__init__.py`
- Create: `e:\Works\Projects\ai\model_train\web\tasks\routes.py`
- Create: `e:\Works\Projects\ai\model_train\web\templates\tasks\list.html`
- Create: `e:\Works\Projects\ai\model_train\web\templates\tasks\detail.html`

- [ ] **Step 1: 创建任务管理路由**

```python
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from web.storage import storage
from datetime import datetime

bp = Blueprint('tasks', __name__, template_folder='templates')


@bp.route('/')
@login_required
def list_tasks():
    """任务列表"""
    tasks = storage.load('tasks')
    tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('tasks/list.html', tasks=tasks)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_task():
    """创建任务"""
    if request.method == 'POST':
        name = request.form.get('name')
        data_file = request.form.get('data_file')
        model_type = request.form.get('model_type')
        
        if not name:
            flash('任务名称不能为空', 'danger')
            return redirect(url_for('tasks.create_task'))
        
        task = {
            'name': name,
            'data_file': data_file,
            'model_type': model_type,
            'status': 'pending',
            'created_by': current_user.email,
            'progress': 0
        }
        
        storage.insert('tasks', task)
        flash('任务创建成功', 'success')
        return redirect(url_for('tasks.list_tasks'))
    
    # 获取可用数据文件
    data_files = storage.load('data_files')
    return render_template('tasks/create.html', data_files=data_files)


@bp.route('/<int:task_id>')
@login_required
def task_detail(task_id):
    """任务详情"""
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('tasks.list_tasks'))
    
    task = tasks[0]
    return render_template('tasks/detail.html', task=task)


@bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """删除任务"""
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('tasks.list_tasks'))
    
    storage.delete('tasks', task_id)
    flash('任务已删除', 'success')
    return redirect(url_for('tasks.list_tasks'))


@bp.route('/<int:task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    """取消任务"""
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('tasks.list_tasks'))
    
    task = tasks[0]
    if task['status'] in ['pending', 'running']:
        storage.update('tasks', task_id, {'status': 'cancelled'})
        flash('任务已取消', 'success')
    else:
        flash('任务无法取消', 'warning')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id))
```

- [ ] **Step 2: 创建任务列表模板**

```html
{% extends "base.html" %}

{% block title %}任务管理 - 模型训练管理系统{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>任务管理</h2>
    <a href="{{ url_for('tasks.create_task') }}" class="btn btn-primary">
        <i class="bi bi-plus-circle"></i> 新建任务
    </a>
</div>

{% if tasks %}
<table class="table table-striped table-hover">
    <thead>
        <tr>
            <th>ID</th>
            <th>名称</th>
            <th>状态</th>
            <th>模型类型</th>
            <th>创建人</th>
            <th>创建时间</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        {% for task in tasks %}
        <tr>
            <td>{{ task._id }}</td>
            <td>{{ task.name }}</td>
            <td>
                {% if task.status == 'pending' %}
                <span class="badge bg-warning">待处理</span>
                {% elif task.status == 'running' %}
                <span class="badge bg-info">运行中</span>
                {% elif task.status == 'completed' %}
                <span class="badge bg-success">已完成</span>
                {% elif task.status == 'failed' %}
                <span class="badge bg-danger">失败</span>
                {% elif task.status == 'cancelled' %}
                <span class="badge bg-secondary">已取消</span>
                {% endif %}
            </td>
            <td>{{ task.model_type or '-' }}</td>
            <td>{{ task.created_by }}</td>
            <td>{{ task.created_at }}</td>
            <td>
                <a href="{{ url_for('tasks.task_detail', task_id=task._id) }}" class="btn btn-sm btn-info">
                    <i class="bi bi-eye"></i> 查看
                </a>
                <form action="{{ url_for('tasks.delete_task', task_id=task._id) }}" method="POST" style="display: inline;">
                    <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('确定删除？')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="alert alert-info">暂无任务</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: 创建任务详情模板**

```html
{% extends "base.html" %}

{% block title %}任务详情 - 模型训练管理系统{% endblock %}

{% block content %}
<div class="mb-4">
    <a href="{{ url_for('tasks.list_tasks') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> 返回
    </a>
</div>

<div class="card">
    <div class="card-header">
        <h4>{{ task.name }}</h4>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <h5>基本信息</h5>
                <table class="table">
                    <tr>
                        <th>任务 ID</th>
                        <td>{{ task._id }}</td>
                    </tr>
                    <tr>
                        <th>状态</th>
                        <td>
                            {% if task.status == 'pending' %}
                            <span class="badge bg-warning">待处理</span>
                            {% elif task.status == 'running' %}
                            <span class="badge bg-info">运行中</span>
                            {% elif task.status == 'completed' %}
                            <span class="badge bg-success">已完成</span>
                            {% elif task.status == 'failed' %}
                            <span class="badge bg-danger">失败</span>
                            {% elif task.status == 'cancelled' %}
                            <span class="badge bg-secondary">已取消</span>
                            {% endif %}
                        </td>
                    </tr>
                    <tr>
                        <th>数据文件</th>
                        <td>{{ task.data_file or '-' }}</td>
                    </tr>
                    <tr>
                        <th>模型类型</th>
                        <td>{{ task.model_type or '-' }}</td>
                    </tr>
                    <tr>
                        <th>创建人</th>
                        <td>{{ task.created_by }}</td>
                    </tr>
                    <tr>
                        <th>创建时间</th>
                        <td>{{ task.created_at }}</td>
                    </tr>
                    {% if task.updated_at %}
                    <tr>
                        <th>更新时间</th>
                        <td>{{ task.updated_at }}</td>
                    </tr>
                    {% endif %}
                </table>
            </div>
            
            <div class="col-md-6">
                <h5>训练结果</h5>
                {% if task.result %}
                <div class="alert alert-success">
                    <strong>模型版本:</strong> {{ task.result.model_version }}<br>
                    <strong>准确率:</strong> {{ task.result.evaluation.accuracy }}<br>
                    <strong>精确率:</strong> {{ task.result.evaluation.precision }}<br>
                    <strong>召回率:</strong> {{ task.result.evaluation.recall }}
                </div>
                {% else %}
                <p class="text-muted">暂无结果</p>
                {% endif %}
            </div>
        </div>
        
        {% if task.status in ['pending', 'running'] %}
        <hr>
        <form action="{{ url_for('tasks.cancel_task', task_id=task._id) }}" method="POST">
            <button type="submit" class="btn btn-warning" onclick="return confirm('确定取消？')">
                <i class="bi bi-x-circle"></i> 取消任务
            </button>
        </form>
        {% endif %}
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: 提交代码**

```bash
git add web/tasks/__init__.py web/tasks/routes.py web/templates/tasks/list.html web/templates/tasks/detail.html
git commit -m "feat: 任务管理功能实现"
```

### 任务 5: 模型管理功能实现

**Files:**
- Create: `e:\Works\Projects\ai\model_train\web\models\__init__.py`
- Create: `e:\Works\Projects\ai\model_train\web\models\routes.py`
- Create: `e:\Works\Projects\ai\model_train\web\templates\models\list.html`
- Create: `e:\Works\Projects\ai\model_train\web\templates\models\detail.html`

- [ ] **Step 1: 创建模型管理路由**

```python
from flask import Blueprint, render_template, redirect, url_for, flash, send_file
from flask_login import login_required
from web.storage import storage
import os

bp = Blueprint('models', __name__, template_folder='templates')


@bp.route('/')
@login_required
def list_models():
    """模型列表"""
    models = storage.load('models')
    models = sorted(models, key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('models/list.html', models=models)


@bp.route('/<int:model_id>')
@login_required
def model_detail(model_id):
    """模型详情"""
    models = storage.find('models', {'_id': model_id})
    if not models:
        flash('模型不存在', 'danger')
        return redirect(url_for('models.list_models'))
    
    model = models[0]
    return render_template('models/detail.html', model=model)


@bp.route('/<int:model_id>/download')
@login_required
def download_model(model_id):
    """下载模型文件"""
    models = storage.find('models', {'_id': model_id})
    if not models:
        flash('模型不存在', 'danger')
        return redirect(url_for('models.list_models'))
    
    model = models[0]
    model_path = model.get('file_path')
    
    if model_path and os.path.exists(model_path):
        return send_file(model_path, as_attachment=True)
    else:
        flash('模型文件不存在', 'danger')
        return redirect(url_for('models.model_detail', model_id=model_id))


@bp.route('/<int:model_id>/delete', methods=['POST'])
@login_required
def delete_model(model_id):
    """删除模型"""
    models = storage.find('models', {'_id': model_id})
    if not models:
        flash('模型不存在', 'danger')
        return redirect(url_for('models.list_models'))
    
    model = models[0]
    model_path = model.get('file_path')
    
    # 删除文件
    if model_path and os.path.exists(model_path):
        os.remove(model_path)
    
    # 删除记录
    storage.delete('models', model_id)
    flash('模型已删除', 'success')
    return redirect(url_for('models.list_models'))
```

- [ ] **Step 2: 创建模型列表模板**

```html
{% extends "base.html" %}

{% block title %}模型管理 - 模型训练管理系统{% endblock %}

{% block content %}
<h2>模型管理</h2>

{% if models %}
<table class="table table-striped table-hover mt-3">
    <thead>
        <tr>
            <th>ID</th>
            <th>名称</th>
            <th>版本</th>
            <th>算法</th>
            <th>准确率</th>
            <th>创建时间</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        {% for model in models %}
        <tr>
            <td>{{ model._id }}</td>
            <td>{{ model.name }}</td>
            <td>v{{ model.version }}</td>
            <td>{{ model.algorithm }}</td>
            <td>
                {% if model.metrics and model.metrics.accuracy %}
                {{ "%.2f"|format(model.metrics.accuracy * 100) }}%
                {% else %}
                -
                {% endif %}
            </td>
            <td>{{ model.created_at }}</td>
            <td>
                <a href="{{ url_for('models.model_detail', model_id=model._id) }}" class="btn btn-sm btn-info">
                    <i class="bi bi-eye"></i> 查看
                </a>
                <a href="{{ url_for('models.download_model', model_id=model._id) }}" class="btn btn-sm btn-primary">
                    <i class="bi bi-download"></i> 下载
                </a>
                <form action="{{ url_for('models.delete_model', model_id=model._id) }}" method="POST" style="display: inline;">
                    <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('确定删除？')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="alert alert-info">暂无模型</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: 创建模型详情模板**

```html
{% extends "base.html" %}

{% block title %}模型详情 - 模型训练管理系统{% endblock %}

{% block content %}
<div class="mb-4">
    <a href="{{ url_for('models.list_models') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> 返回
    </a>
</div>

<div class="card">
    <div class="card-header">
        <h4>{{ model.name }} (v{{ model.version }})</h4>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <h5>基本信息</h5>
                <table class="table">
                    <tr>
                        <th>模型 ID</th>
                        <td>{{ model._id }}</td>
                    </tr>
                    <tr>
                        <th>算法</th>
                        <td>{{ model.algorithm }}</td>
                    </tr>
                    <tr>
                        <th>版本</th>
                        <td>{{ model.version }}</td>
                    </tr>
                    <tr>
                        <th>文件路径</th>
                        <td>{{ model.file_path or '-' }}</td>
                    </tr>
                    <tr>
                        <th>创建时间</th>
                        <td>{{ model.created_at }}</td>
                    </tr>
                </table>
            </div>
            
            <div class="col-md-6">
                <h5>评估指标</h5>
                {% if model.metrics %}
                <div class="alert alert-success">
                    <strong>准确率:</strong> {{ "%.2f"|format(model.metrics.accuracy * 100) }}%<br>
                    <strong>精确率:</strong> {{ "%.2f"|format(model.metrics.precision * 100) }}%<br>
                    <strong>召回率:</strong> {{ "%.2f"|format(model.metrics.recall * 100) }}%
                </div>
                {% else %}
                <p class="text-muted">暂无评估数据</p>
                {% endif %}
            </div>
        </div>
        
        <hr>
        
        <a href="{{ url_for('models.download_model', model_id=model._id) }}" class="btn btn-primary">
            <i class="bi bi-download"></i> 下载模型
        </a>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: 提交代码**

```bash
git add web/models/__init__.py web/models/routes.py web/templates/models/list.html web/templates/models/detail.html
git commit -m "feat: 模型管理功能实现"
```

### 任务 6: 数据管理功能实现

**Files:**
- Create: `e:\Works\Projects\ai\model_train\web\data\__init__.py`
- Create: `e:\Works\Projects\ai\model_train\web\data\routes.py`
- Create: `e:\Works\Projects\ai\model_train\web\templates\data\list.html`
- Create: `e:\Works\Projects\ai\model_train\web\templates\data\upload.html`

- [ ] **Step 1: 创建数据管理路由**

```python
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from web.storage import storage
import os
import pandas as pd

bp = Blueprint('data', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = {'csv', 'json'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
@login_required
def list_data():
    """数据文件列表"""
    data_files = storage.load('data_files')
    data_files = sorted(data_files, key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('data/list.html', data_files=data_files)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_data():
    """上传数据文件"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(url_for('data.upload_data'))
        
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(url_for('data.upload_data'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # 记录到存储
            data_file = {
                'filename': filename,
                'file_path': file_path,
                'uploaded_by': current_user.email,
                'size': os.path.getsize(file_path)
            }
            
            # 如果是 CSV，尝试读取基本信息
            if filename.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path, nrows=5)
                    data_file['preview'] = df.to_html(classes='table table-sm', index=False)
                    data_file['rows'] = len(pd.read_csv(file_path))
                    data_file['columns'] = list(df.columns)
                except Exception as e:
                    flash(f'无法解析 CSV 文件：{str(e)}', 'warning')
            
            storage.insert('data_files', data_file)
            flash('文件上传成功', 'success')
            return redirect(url_for('data.list_data'))
        else:
            flash('不支持的文件格式，请上传 CSV 或 JSON 文件', 'danger')
    
    return render_template('data/upload.html')


@bp.route('/<int:file_id>')
@login_required
def data_detail(file_id):
    """数据文件详情"""
    data_files = storage.find('data_files', {'_id': file_id})
    if not data_files:
        flash('文件不存在', 'danger')
        return redirect(url_for('data.list_data'))
    
    data_file = data_files[0]
    return render_template('data/detail.html', data_file=data_file)


@bp.route('/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_data(file_id):
    """删除数据文件"""
    data_files = storage.find('data_files', {'_id': file_id})
    if not data_files:
        flash('文件不存在', 'danger')
        return redirect(url_for('data.list_data'))
    
    data_file = data_files[0]
    file_path = data_file.get('file_path')
    
    # 删除文件
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # 删除记录
    storage.delete('data_files', file_id)
    flash('文件已删除', 'success')
    return redirect(url_for('data.list_data'))
```

- [ ] **Step 2: 创建数据文件列表模板**

```html
{% extends "base.html" %}

{% block title %}数据管理 - 模型训练管理系统{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>数据管理</h2>
    <a href="{{ url_for('data.upload_data') }}" class="btn btn-primary">
        <i class="bi bi-upload"></i> 上传文件
    </a>
</div>

{% if data_files %}
<table class="table table-striped table-hover">
    <thead>
        <tr>
            <th>ID</th>
            <th>文件名</th>
            <th>大小</th>
            <th>行数</th>
            <th>上传人</th>
            <th>上传时间</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        {% for file in data_files %}
        <tr>
            <td>{{ file._id }}</td>
            <td>{{ file.filename }}</td>
            <td>{{ "%.2f"|format(file.size / 1024) }} KB</td>
            <td>{{ file.rows or '-' }}</td>
            <td>{{ file.uploaded_by }}</td>
            <td>{{ file.created_at }}</td>
            <td>
                <a href="{{ url_for('data.data_detail', file_id=file._id) }}" class="btn btn-sm btn-info">
                    <i class="bi bi-eye"></i> 查看
                </a>
                <form action="{{ url_for('data.delete_data', file_id=file._id) }}" method="POST" style="display: inline;">
                    <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('确定删除？')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="alert alert-info">暂无数据文件</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: 创建上传模板**

```html
{% extends "base.html" %}

{% block title %}上传数据 - 模型训练管理系统{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h4>上传数据文件</h4>
            </div>
            <div class="card-body">
                <form method="POST" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label for="file" class="form-label">选择文件</label>
                        <input type="file" class="form-control" id="file" name="file" required>
                        <div class="form-text">支持 CSV 和 JSON 格式，最大 16MB</div>
                    </div>
                    
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-upload"></i> 上传
                        </button>
                    </div>
                </form>
                
                <hr>
                
                <a href="{{ url_for('data.list_data') }}" class="btn btn-secondary">
                    <i class="bi bi-arrow-left"></i> 返回
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: 提交代码**

```bash
git add web/data/__init__.py web/data/routes.py web/templates/data/list.html web/templates/data/upload.html
git commit -m "feat: 数据管理功能实现"
```

### 任务 7: API 接口和集成测试

**Files:**
- Create: `e:\Works\Projects\ai\model_train\web\api\__init__.py`
- Create: `e:\Works\Projects\ai\model_train\web\api\routes.py`
- Create: `e:\Works\Projects\ai\model_train\tests\test_web.py`

- [ ] **Step 1: 创建 API 路由**

```python
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from web.storage import storage
from datetime import datetime

bp = Blueprint('api', __name__)


@bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """获取任务列表"""
    tasks = storage.load('tasks')
    return jsonify(tasks)


@bp.route('/tasks', methods=['POST'])
@login_required
def create_task_api():
    """创建任务 API"""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': '任务名称不能为空'}), 400
    
    task = {
        'name': data['name'],
        'data_file': data.get('data_file'),
        'model_type': data.get('model_type'),
        'status': 'pending',
        'created_by': current_user.email,
        'progress': 0
    }
    
    task_id = storage.insert('tasks', task)
    return jsonify({'id': task_id, 'message': '任务创建成功'}), 201


@bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """获取任务详情"""
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(tasks[0])


@bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """更新任务状态"""
    data = request.get_json()
    tasks = storage.find('tasks', {'_id': task_id})
    
    if not tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    updates = {}
    if 'status' in data:
        updates['status'] = data['status']
    if 'progress' in data:
        updates['progress'] = data['progress']
    if 'result' in data:
        updates['result'] = data['result']
    
    storage.update('tasks', task_id, updates)
    return jsonify({'message': '任务已更新'})


@bp.route('/models', methods=['GET'])
@login_required
def get_models():
    """获取模型列表"""
    models = storage.load('models')
    return jsonify(models)


@bp.route('/data', methods=['GET'])
@login_required
def get_data_files():
    """获取数据文件列表"""
    data_files = storage.load('data_files')
    return jsonify(data_files)
```

- [ ] **Step 2: 创建集成测试**

```python
import pytest
from web import create_app
from web.storage import init_storage
import tempfile
import os


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    
    # 使用临时目录存储
    with tempfile.TemporaryDirectory() as tmpdir:
        init_storage(tmpdir)
        yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试器"""
    return app.test_cli_runner()


def test_login_page(client):
    """测试登录页面"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'用户登录' in response.data


def test_register_page(client):
    """测试注册页面"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'用户注册' in response.data


def test_dashboard_requires_login(client):
    """测试仪表板需要登录"""
    response = client.get('/dashboard/', follow_redirects=True)
    assert response.status_code == 200
    assert b'请登录' in response.data


def test_create_task_api_requires_login(client):
    """测试创建任务 API 需要登录"""
    response = client.post('/api/tasks', json={'name': 'Test Task'})
    assert response.status_code == 302  # 重定向到登录


def test_tasks_list_requires_login(client):
    """测试任务列表需要登录"""
    response = client.get('/tasks/', follow_redirects=True)
    assert response.status_code == 200
    assert b'请登录' in response.data
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_web.py -v
```

Expected output:
```
tests/test_web.py::test_login_page PASSED
tests/test_web.py::test_register_page PASSED
tests/test_web.py::test_dashboard_requires_login PASSED
tests/test_web.py::test_create_task_api_requires_login PASSED
tests/test_web.py::test_tasks_list_requires_login PASSED
```

- [ ] **Step 4: 提交代码**

```bash
git add web/api/__init__.py web/api/routes.py tests/test_web.py
git commit -m "feat: API 接口和集成测试实现"
```

### 任务 8: 与训练系统集成

**Files:**
- Modify: `e:\Works\Projects\ai\model_train\src\task_manager.py`
- Create: `e:\Works\Projects\ai\model_train\web\services\training_service.py`

- [ ] **Step 1: 创建训练服务**

```python
from src.trainer import Trainer
from src.result_processor import ResultProcessor
from web.storage import storage
import os


class TrainingService:
    """训练服务"""
    
    def __init__(self):
        self.trainer = Trainer()
        self.result_processor = ResultProcessor()
    
    def execute_task(self, task_id):
        """执行训练任务"""
        # 获取任务信息
        tasks = storage.find('tasks', {'_id': task_id})
        if not tasks:
            return False
        
        task = tasks[0]
        
        # 更新任务状态为运行中
        storage.update('tasks', task_id, {'status': 'running', 'progress': 10})
        
        try:
            # 执行训练
            storage.update('tasks', task_id, {'<think>
</think>

我已经完成了 Web 管理界面的详细实现计划！计划文档已保存到：

`e:\Works\Projects\ai\model_train\docs\superpowers\plans\2026-04-16-web-admin-implementation.md`

## 总结

### 参考项目的好功能（已标记为 TODO）

我从 MLflow 等项目中总结了以下功能，按优先级标记为 TODO：

**高优先级 TODO:**
- 🔮 模型预测功能
- 📊 实验跟踪
- 📈 数据可视化
- 📝 模型注册表

**中优先级 TODO:**
- ⚙️ 超参数调优
- 🚀 模型导出
- 📱 高级监控
- 📄 报告生成

**低优先级 TODO:**
- 👥 用户协作功能
- 🤖 自动化功能
- 🔔 训练任务通知

### 实现计划包含 8 个主要任务

1. **项目结构搭建** - Flask 应用工厂、配置、存储管理
2. **用户认证系统** - 登录/注册、权限管理
3. **基础模板和仪表板** - Bootstrap 5 界面、统计展示
4. **任务管理功能** - 任务列表、创建、详情、取消
5. **模型管理功能** - 模型列表、详情、下载
6. **数据管理功能** - 文件上传、预览、删除
7. **API 接口** - RESTful API 供前端调用
8. **与训练系统集成** - 连接后台训练系统

### 执行选项

**计划已完成并保存。两种执行方式：**

**1. Subagent-Driven（推荐）** - 我为每个任务分配新的子代理，在任务之间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中使用 executing-plans 技能执行任务，批量执行并设置检查点

您更倾向于哪种执行方式？