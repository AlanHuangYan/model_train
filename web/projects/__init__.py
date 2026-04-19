from flask import Blueprint
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from web.storage import storage
import os
from datetime import datetime

bp = Blueprint('projects', __name__, template_folder='../templates')

class Project:
    """项目模型"""
    
    def __init__(self, id, name, english_name, description='', created_by=None, created_at=None):
        self.id = id
        self.name = name
        self.english_name = english_name  # 用于创建目录
        self.description = description
        self.created_by = created_by
        self.created_at = created_at
    
    @staticmethod
    def get(project_id):
        """根据 ID 获取项目"""
        from web.storage import storage
        if not storage:
            return None
        projects = storage.find('projects', {'_id': project_id})
        if not projects:
            return None
        project_data = projects[0]
        return Project(
            id=project_data['_id'],
            name=project_data['name'],
            english_name=project_data['english_name'],
            description=project_data.get('description', ''),
            created_by=project_data.get('created_by'),
            created_at=project_data.get('created_at')
        )
    
    @staticmethod
    def get_all():
        """获取所有项目"""
        from web.storage import storage
        if not storage:
            return []
        projects = storage.find('projects', {})
        return [
            Project(
                id=p['_id'],
                name=p['name'],
                english_name=p['english_name'],
                description=p.get('description', ''),
                created_by=p.get('created_by'),
                created_at=p.get('created_at')
            ) for p in projects
        ]
    
    @staticmethod
    def find_by_english_name(english_name):
        """根据英文名称查找项目"""
        from web.storage import storage
        if not storage:
            return None
        projects = storage.find('projects', {'english_name': english_name})
        if not projects:
            return None
        project_data = projects[0]
        return Project(
            id=project_data['_id'],
            name=project_data['name'],
            english_name=project_data['english_name'],
            description=project_data.get('description', ''),
            created_by=project_data.get('created_by'),
            created_at=project_data.get('created_at')
        )
    
    @staticmethod
    def create(name, english_name, description='', created_by=None):
        """创建项目"""
        from web.storage import storage
        import os
        from datetime import datetime
        
        # 检查英文名是否已存在
        existing = storage.find('projects', {'english_name': english_name})
        if existing:
            return None
        
        project_data = {
            'name': name,
            'english_name': english_name,
            'description': description,
            'created_by': created_by,
            'created_at': datetime.now().isoformat()
        }
        
        if storage:
            project_id = storage.insert('projects', project_data)
            
            # 创建项目目录
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', english_name)
            os.makedirs(data_dir, exist_ok=True)
            
            return project_id
        return None
    
    @staticmethod
    def delete(project_id):
        """删除项目"""
        from web.storage import storage
        import shutil
        import glob
        import os
        
        projects = storage.find('projects', {'_id': project_id})
        if not projects:
            return False
        
        project = projects[0]
        english_name = project.get('english_name')
        
        # 获取项目下所有任务
        tasks = storage.find('tasks', {'project_id': project_id})
        task_ids = [t['_id'] for t in tasks]
        
        # 删除任务的对比历史记录
        for task_id in task_ids:
            compare_records = storage.find('compare_history', {'task_id': task_id})
            for record in compare_records:
                storage.delete('compare_history', record['_id'])
        
        # 删除任务
        for task_id in task_ids:
            storage.delete('tasks', task_id)
        
        # 删除项目的数据文件
        data_files = storage.find('data_files', {'project_id': project_id})
        for df in data_files:
            storage.delete('data_files', df['_id'])
        
        # 删除项目的模型
        models = storage.find('models', {'project_id': project_id})
        for m in models:
            storage.delete('models', m['_id'])
        
        # 删除任务的日志文件
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        for task_id in task_ids:
            for log_file in glob.glob(os.path.join(log_dir, f'task_{task_id}*.log')):
                try:
                    os.remove(log_file)
                except OSError:
                    pass
        
        # 删除项目目录
        if english_name:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', english_name)
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
        
        # 删除项目记录
        storage.delete('projects', project_id)
        return True


# Import routes at the end to avoid circular imports
from web.projects import routes
