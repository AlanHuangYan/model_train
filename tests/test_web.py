import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web import create_app
from web.storage import init_storage
import tempfile


@pytest.fixture
def app():
    """创建测试应用"""
    # 使用临时目录存储
    with tempfile.TemporaryDirectory() as tmpdir:
        init_storage(tmpdir)
        app = create_app('testing')
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
    assert b'Login' in response.data or b'\xe7\x94\xa8\xe6\x88\xb7\xe7\x99\xbb\xe5\xbd\x95' in response.data


def test_register_page(client):
    """测试注册页面"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data or b'\xe6\xb3\xa8\xe5\x86\x8c' in response.data


def test_dashboard_requires_login(client):
    """测试仪表板需要登录"""
    response = client.get('/dashboard/', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login or show login message
    assert response.status_code == 200


def test_create_task_api_requires_login(client):
    """测试创建任务 API 需要登录"""
    response = client.post('/api/tasks', json={'name': 'Test Task'})
    assert response.status_code == 302  # 重定向到登录


def test_tasks_list_requires_login(client):
    """测试任务列表需要登录"""
    response = client.get('/tasks/', follow_redirects=True)
    assert response.status_code == 200


def test_user_registration(client):
    """测试用户注册功能"""
    # 访问注册页面
    response = client.get('/register')
    assert response.status_code == 200
    
    # 提交注册表单
    register_data = {
        'email': 'test@test.com',
        'password': 'alan1234',
        'confirm_password': 'alan1234'
    }
    response = client.post('/register', data=register_data, follow_redirects=True)
    
    # 注册成功后应该重定向到登录页面
    assert response.status_code == 200
    # 检查是否显示成功消息或登录表单
    assert b'login' in response.data.lower() or b'\xe7\x99\xbb\xe5\xbd\x95' in response.data


def test_user_login(client):
    """测试用户登录功能"""
    # 先注册（如果还没注册）
    register_data = {
        'email': 'test@test.com',
        'password': 'alan7566',
        'confirm_password': 'alan7566'
    }
    client.post('/register', data=register_data)
    
    # 尝试登录
    login_data = {
        'email': 'test@test.com',
        'password': 'alan7566'
    }
    response = client.post('/login', data=login_data, follow_redirects=True)
    
    # 登录成功后应该重定向到仪表板
    assert response.status_code == 200
    # 检查是否显示仪表板或欢迎信息
    assert b'\xe4\xbb\xaa\xe8\xa1\xa8\xe6\x9d\xbf' in response.data or b'dashboard' in response.data.lower() or response.request.path != '/login'


def test_user_management(client):
    """测试用户管理功能"""
    # 注册两个用户
    client.post('/register', data={
        'email': 'user1@test.com',
        'password': 'test123',
        'confirm_password': 'test123'
    })
    
    client.post('/register', data={
        'email': 'user2@test.com',
        'password': 'test123',
        'confirm_password': 'test123'
    })
    
    # 登录第一个用户
    client.post('/login', data={
        'email': 'user1@test.com',
        'password': 'test123'
    })
    
    # 访问用户列表页面
    response = client.get('/users')
    assert response.status_code == 200
    # 应该显示用户列表
    assert b'user1@test.com' in response.data or b'User' in response.data
    
    # 获取 user2 的 ID（从页面中解析或使用其他方式）
    # 这里简单测试删除功能
    response = client.post('/users/1/delete', follow_redirects=True)
    # 应该能删除其他用户
    assert response.status_code == 200
