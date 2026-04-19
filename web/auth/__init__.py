from flask import Blueprint
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from web.storage import storage

bp = Blueprint('auth', __name__, template_folder='../templates')

class User(UserMixin):
    """用户模型"""
    
    def __init__(self, id, email, password_hash, is_admin=False, created_at=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = created_at
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get(user_id):
        """根据 ID 获取用户"""
        from web.storage import storage
        if not storage:
            return None
        users = storage.find('users', {'_id': user_id})
        if not users:
            return None
        user_data = users[0]
        return User(
            id=user_data['_id'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            is_admin=user_data.get('is_admin', False),
            created_at=user_data.get('created_at')
        )
    
    @staticmethod
    def find_by_email(email):
        """根据邮箱查找用户"""
        from web.storage import storage
        if not storage:
            return None
        users = storage.find('users', {'email': email})
        if not users:
            return None
        user_data = users[0]
        return User(
            id=user_data['_id'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            is_admin=user_data.get('is_admin', False),
            created_at=user_data.get('created_at')
        )
    
    @staticmethod
    def create(email, password, is_admin=False):
        """创建用户"""
        from web.storage import storage
        from datetime import datetime
        user_data = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_admin': is_admin,
            'active': True,
            'created_at': datetime.now().isoformat()
        }
        if storage:
            storage.insert('users', user_data)
    
    @staticmethod
    def get_all(page=1, per_page=10):
        """获取所有用户（分页）"""
        from web.storage import storage
        if not storage:
            return [], 0, 0
        
        all_users = storage.find('users', {})
        total = len(all_users)
        total_pages = (total + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        users_page = all_users[start:end]
        
        return [
            User(
                id=u['_id'],
                email=u['email'],
                password_hash=u['password_hash'],
                is_admin=u.get('is_admin', False),
                created_at=u.get('created_at')
            ) for u in users_page
        ], page, total_pages
    
    @staticmethod
    def delete(user_id):
        """删除用户"""
        from web.storage import storage
        if not storage:
            return False
        
        users = storage.find('users', {'_id': user_id})
        if not users:
            return False
        
        storage.delete('users', {'_id': user_id})
        return True


# Import routes at the end to avoid circular imports
from web.auth import routes
