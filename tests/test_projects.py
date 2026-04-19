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
    # 先注册
    client.post('/register', data={
        'email': 'test@test.com',
        'password': 'test123',
        'confirm_password': 'test123'
    })
    # 登录
    client.post('/login', data={
        'email': 'test@test.com',
        'password': 'test123'
    })
    return client


def test_create_project(logged_in_client):
    """测试创建项目"""
    response = logged_in_client.post('/projects/create', data={
        'name': '酒店客服训练',
        'english_name': 'hotel_customer_service',
        'description': '酒店客服对话模型训练'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'hotel_customer_service' in response.data or b'project' in response.data.lower()


def test_list_projects(logged_in_client):
    """测试项目列表"""
    # 先创建项目
    logged_in_client.post('/projects/create', data={
        'name': 'Test Project',
        'english_name': 'test_project',
        'description': 'Test description'
    })
    
    response = logged_in_client.get('/projects/', follow_redirects=True)
    assert response.status_code == 200
    assert b'test_project' in response.data or b'project' in response.data.lower()


def test_project_detail(logged_in_client):
    """测试项目详情"""
    # 创建项目
    logged_in_client.post('/projects/create', data={
        'name': 'Detail Test',
        'english_name': 'detail_test',
        'description': 'Test detail'
    })
    
    response = logged_in_client.get('/projects/1')
    assert response.status_code == 200


def test_delete_project(logged_in_client):
    """测试删除项目"""
    # 创建项目
    logged_in_client.post('/projects/create', data={
        'name': 'Delete Test',
        'english_name': 'delete_test',
        'description': 'Test delete'
    })
    
    response = logged_in_client.post('/projects/1/delete', follow_redirects=True)
    assert response.status_code == 200
