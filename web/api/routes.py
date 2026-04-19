from flask import jsonify, request
from flask_login import login_required, current_user
from web.api import bp
from web.storage import storage
from datetime import datetime


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
