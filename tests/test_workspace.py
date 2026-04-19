import pytest
from web import create_app
from web.storage import init_storage
import tempfile


@pytest.fixture
def app():
    """创建测试应用"""
    with tempfile.TemporaryDirectory() as tmpdir:
        init_storage(tmpdir)
        app = create_app('testing')
        yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    """已登录的测试客户端"""
    client.post('/register', data={
        'email': 'test@test.com',
        'password': 'test123',
        'confirm_password': 'test123'
    })
    client.post('/login', data={
        'email': 'test@test.com',
        'password': 'test123'
    })
    return client


def test_project_portal(logged_in_client):
    """测试项目门户"""
    response = logged_in_client.get('/projects/')
    assert response.status_code == 200
    assert b'portal' in response.data.lower() or b'project' in response.data.lower()


def test_project_workspace(logged_in_client):
    """测试项目空间"""
    # 先创建项目
    logged_in_client.post('/projects/create', data={
        'name': 'Test Project',
        'english_name': 'test_project',
        'description': 'Test'
    })
    
    # 进入项目空间
    response = logged_in_client.get('/projects/1/workspace', follow_redirects=True)
    assert response.status_code == 200
    assert b'dashboard' in response.data.lower() or b'project' in response.data.lower()
