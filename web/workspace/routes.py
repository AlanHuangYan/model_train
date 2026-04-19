from flask import render_template, session, request, flash, redirect, url_for
from flask_login import login_required, current_user
from web.workspace import bp
from web.storage import storage
import os
import sys
import glob
from datetime import datetime

# 全局日志函数
def log_message(message, level='INFO', task_id=None):
    """同时输出到控制台和日志文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f'[{timestamp}] [{level}] {message}'
    print(log_line)
    
    # 如果有 task_id，写入对应的日志文件
    if task_id:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            log_dir = os.path.join(base_dir, 'logs')
            log_file = os.path.join(log_dir, f'task_{task_id}.log')
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception:
            pass

@bp.route('/<int:project_id>/dashboard')
@login_required
def dashboard(project_id):
    """项目空间仪表盘"""
    from web.projects import Project
    
    # 获取当前项目
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    # 获取项目统计数据
    tasks = storage.find('tasks', {'project_id': project_id})
    models = storage.find('models', {'project_id': project_id})
    data_files = storage.find('data_files', {'project_id': project_id})
    
    stats = {
        'task_count': len(tasks),
        'running_tasks': len([t for t in tasks if t.get('status') == 'running']),
        'model_count': len(models),
        'latest_model': models[0].get('name') if models else None,
        'data_count': len(data_files),
        'total_data_size': sum(f.get('size', 0) for f in data_files)
    }
    
    # 转换大小单位
    if stats['total_data_size']:
        stats['total_data_size'] = f"{stats['total_data_size'] / (1024*1024):.2f} MB"
    
    # 最近任务
    recent_tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    # 最近模型
    recent_models = sorted(models, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    return render_template('workspace/dashboard.html',
                         current_project=current_project,
                         stats=stats,
                         recent_tasks=recent_tasks,
                         recent_models=recent_models)

@bp.route('/<int:project_id>/tasks')
@login_required
def tasks(project_id):
    """项目任务管理"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    # 获取该项目的任务
    tasks = storage.find('tasks', {'project_id': project_id})
    
    # 为每个任务添加基础模型信息
    for task in tasks:
        if task.get('model_id') and not task.get('base_model'):
            models = storage.find('models', {'_id': task['model_id']})
            if models:
                task['base_model'] = models[0].get('base_model')
    
    tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('workspace/tasks/list.html',
                         tasks=tasks,
                         current_project=current_project)

@bp.route('/<int:project_id>/models')
@login_required
def models(project_id):
    """项目模型管理"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    # 获取该项目的模型
    models = storage.find('models', {'project_id': project_id})
    models = sorted(models, key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('workspace/models/list.html',
                         models=models,
                         current_project=current_project)

@bp.route('/<int:project_id>/data')
@login_required
def data(project_id):
    """项目数据管理"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    # 获取该项目的数据
    data_files = storage.find('data_files', {'project_id': project_id})
    data_files = sorted(data_files, key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('workspace/data/list.html',
                         data_files=data_files,
                         current_project=current_project)

@bp.route('/<int:project_id>/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    """创建任务（项目空间内）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        data_file = request.form.get('data_file')
        model_id = request.form.get('model_id')
        base_model = request.form.get('base_model')
        use_gpu = request.form.get('use_gpu', 'auto')
        merge_model = request.form.get('merge_model') == 'true'
        
        if not name:
            flash('任务名称不能为空', 'danger')
            return redirect(url_for('workspace.create_task', project_id=project_id))
        
        # 将 model_id 转换为整数，与 models._id 类型保持一致
        if model_id:
            try:
                model_id = int(model_id)
                # 根据 model_id 查询对应的 base_model
                models = storage.find('models', {'_id': model_id})
                if models:
                    base_model = models[0].get('base_model')
                    log_message(f'根据 model_id={model_id} 查询到 base_model={base_model}')
                else:
                    log_message(f'未找到 model_id={model_id} 的模型记录', 'WARNING')
                    base_model = None
            except (ValueError, TypeError):
                model_id = None
                base_model = None
        
        task = {
            'name': name,
            'project_id': project_id,
            'data_file': data_file,
            'model_id': model_id,
            'base_model': base_model,
            'use_gpu': use_gpu,
            'merge_model': merge_model,
            'status': 'pending',
            'created_by': current_user.email,
            'progress': 0
        }
        
        storage.insert('tasks', task)
        flash('任务创建成功', 'success')
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    # 获取可用数据文件、模型和基础模型
    import os
    data_files = storage.find('data_files', {'project_id': project_id})
    models = storage.find('models', {'project_id': project_id})
    
    # 扫描本地 models 目录
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    models_dir = os.path.join(base_dir, 'models')
    available_models = []
    if os.path.exists(models_dir):
        for model_name in os.listdir(models_dir):
            model_path = os.path.join(models_dir, model_name)
            if os.path.isdir(model_path) and os.path.exists(os.path.join(model_path, 'config.json')):
                available_models.append({
                    'name': model_name,
                    'path': f'models/{model_name}'
                })
    
    return render_template('workspace/tasks/create.html',
                         data_files=data_files,
                         models=models,
                         available_models=available_models,
                         current_project=current_project)

@bp.route('/<int:project_id>/data/upload', methods=['GET', 'POST'])
@login_required
def upload_data(project_id):
    """上传数据（项目空间内）"""
    from web.projects import Project
    from werkzeug.utils import secure_filename
    from flask import current_app
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        if 'file' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(url_for('workspace.upload_data', project_id=project_id))
        
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(url_for('workspace.upload_data', project_id=project_id))
        
        if not name:
            flash('数据名称不能为空', 'danger')
            return redirect(url_for('workspace.upload_data', project_id=project_id))
        
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ['csv', 'json', 'jsonl']:
            filename = secure_filename(file.filename)
            
            # 上传到项目目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            upload_folder = os.path.join(base_dir, 'data', current_project.english_name, 'raw')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # 调试信息：打印路径
            print(f"Base dir: {base_dir}")
            print(f"Upload folder: {upload_folder}")
            print(f"File path: {file_path}")
            print(f"Project english_name: {current_project.english_name}")
            
            # 记录到存储
            data_file = {
                'name': name,
                'filename': filename,
                'file_path': file_path,
                'project_id': project_id,
                'uploaded_by': current_user.email,
                'size': os.path.getsize(file_path)
            }
            
            storage.insert('data_files', data_file)
            flash('数据文件上传成功', 'success')
            return redirect(url_for('workspace.data', project_id=project_id))
    
    return render_template('workspace/data/upload.html',
                         current_project=current_project,
                         form=None)

@bp.route('/<int:project_id>/models/create', methods=['GET', 'POST'])
@login_required
def create_model(project_id):
    """创建模型（项目空间内）"""
    from web.projects import Project
    import os
    
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    # 扫描本地 models 目录，获取可用模型
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    models_dir = os.path.join(base_dir, 'models')
    available_models = []
    if os.path.exists(models_dir):
        for model_name in os.listdir(models_dir):
            model_path = os.path.join(models_dir, model_name)
            if os.path.isdir(model_path) and os.path.exists(os.path.join(model_path, 'config.json')):
                available_models.append({
                    'name': model_name,
                    'path': f'models/{model_name}'
                })
    
    if request.method == 'POST':
        name = request.form.get('name')
        base_model = request.form.get('base_model')
        description = request.form.get('description')
        
        if not name:
            flash('模型名称不能为空', 'danger')
            return redirect(url_for('workspace.create_model', project_id=project_id))
        
        if not base_model:
            flash('请选择基础模型', 'danger')
            return redirect(url_for('workspace.create_model', project_id=project_id))
        
        model = {
            'name': name,
            'base_model': base_model,
            'description': description,
            'project_id': project_id,
            'created_by': current_user.email
        }
        
        storage.insert('models', model)
        flash('模型创建成功', 'success')
        return redirect(url_for('workspace.models', project_id=project_id))
    
    return render_template('workspace/models/create.html',
                         available_models=available_models,
                         current_project=current_project)

@bp.route('/<int:project_id>/data/<int:file_id>')
@login_required
def data_detail(project_id, file_id):
    """数据文件详情（项目空间内）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    data_files = storage.find('data_files', {'_id': file_id})
    if not data_files:
        flash('文件不存在', 'danger')
        return redirect(url_for('workspace.data', project_id=project_id))
    
    data_file = data_files[0]
    return render_template('workspace/data/detail.html',
                         data_file=data_file,
                         current_project=current_project)

@bp.route('/<int:project_id>/data/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_data(project_id, file_id):
    """删除数据文件（项目空间内）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    data_files = storage.find('data_files', {'_id': file_id})
    if not data_files:
        flash('文件不存在', 'danger')
        return redirect(url_for('workspace.data', project_id=project_id))
    
    data_file = data_files[0]
    file_path = data_file.get('file_path')
    
    # 删除文件
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # 删除记录
    storage.delete('data_files', file_id)
    flash('文件已删除', 'success')
    return redirect(url_for('workspace.data', project_id=project_id))

@bp.route('/<int:project_id>/tasks/<int:task_id>')
@login_required
def task_detail(project_id, task_id):
    """任务详情（项目空间内）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    task = tasks[0]
    # 如果有 model_id 但没有 base_model，查询模型信息
    if task.get('model_id') and not task.get('base_model'):
        models = storage.find('models', {'_id': task['model_id']})
        if models:
            task['base_model'] = models[0].get('base_model')
    return render_template('workspace/tasks/detail.html',
                         task=task,
                         current_project=current_project)

@bp.route('/<int:project_id>/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(project_id, task_id):
    """删除任务（项目空间内）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    # 删除任务的对比历史记录
    compare_records = storage.find('compare_history', {'task_id': task_id})
    for record in compare_records:
        storage.delete('compare_history', record['_id'])
    if compare_records:
        log_message(f'已删除任务 {task_id} 的 {len(compare_records)} 条对比历史记录', task_id=task_id)
    
    # 删除任务的日志文件
    import glob
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    for log_file in glob.glob(os.path.join(log_dir, f'task_{task_id}*.log')):
        try:
            os.remove(log_file)
        except OSError:
            pass
    
    storage.delete('tasks', task_id)
    flash('任务已删除', 'success')
    return redirect(url_for('workspace.tasks', project_id=project_id))

@bp.route('/<int:project_id>/tasks/<int:task_id>/start', methods=['GET'])
@login_required
def start_training(project_id, task_id):
    """开始训练（项目空间内）"""
    from web.projects import Project
    import subprocess
    
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    task = tasks[0]
    log_message(f'开始处理任务 {task_id}: {task.get("name")}', task_id=task_id)
    log_message(f'任务状态：{task["status"]}', task_id=task_id)
    
    # 允许运行 pending、failed、cancelled 状态的任务
    if task['status'] not in ['pending', 'failed', 'cancelled']:
        log_message(f'任务状态不允许运行：{task["status"]}', 'WARNING', task_id=task_id)
        flash('该任务无法开始训练', 'warning')
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    # 更新任务状态为运行中
    storage.update('tasks', task_id, {'status': 'running', 'progress': 0, 'error': None})
    log_message('任务状态已更新为 running', task_id=task_id)
    
    # 获取训练参数
    data_file = task.get('data_file')
    model_id = task.get('model_id')
    base_model = task.get('base_model')
    use_gpu = task.get('use_gpu', 'auto')
    merge_model = task.get('merge_model', False)
    log_message(f'训练参数：data_file={data_file}, model_id={model_id}, base_model={base_model}, use_gpu={use_gpu}, merge_model={merge_model}', task_id=task_id)
    
    # 获取数据文件路径
    data_files = storage.find('data_files', {'filename': data_file})
    if not data_files:
        error_msg = f'数据文件不存在：{data_file}'
        log_message(error_msg, 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
        storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    data_file_record = data_files[0]
    data_file_path = data_file_record.get('file_path')
    log_message(f'数据文件路径：{data_file_path}', task_id=task_id)
    
    # 获取模型路径
    if model_id:
        log_message(f'查询模型记录，model_id={model_id}', task_id=task_id)
        models = storage.find('models', {'_id': model_id})
        log_message(f'查询结果：找到 {len(models)} 条记录', task_id=task_id)
        if models:
            model_path = models[0].get('base_model')
            log_message(f'模型记录详情：{models[0]}', task_id=task_id)
            log_message(f'使用模型记录的基础模型：{model_path}', task_id=task_id)
        else:
            model_path = base_model
            log_message(f'模型记录不存在，使用 base_model: {model_path}', 'WARNING', task_id=task_id)
            # 尝试查询所有模型记录
            all_models = storage.find('models', {})
            log_message(f'当前所有模型记录数：{len(all_models)}', task_id=task_id)
            for i, m in enumerate(all_models):
                log_message(f'模型 {i}: ID={m.get("_id")}, name={m.get("name")}, base_model={m.get("base_model")}', task_id=task_id)
    else:
        model_path = base_model
        log_message(f'使用 base_model: {model_path}', task_id=task_id)
    
    if not model_path:
        error_msg = '未指定基础模型'
        log_message(error_msg, 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
        storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    # 项目根目录（web 目录的父目录）
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    log_message(f'项目根目录：{base_dir}', task_id=task_id)
    
    # 数据目录（包含 train.jsonl, val.jsonl）
    data_dir = os.path.join(base_dir, 'data', current_project.english_name)
    if not os.path.exists(data_dir):
        error_msg = f'数据目录不存在：{data_dir}'
        log_message(error_msg, 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
        storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
        return redirect(url_for('workspace.tasks', project_id=project_id))
    log_message(f'数据目录：{data_dir}', task_id=task_id)
    
    # 输出目录
    output_dir = os.path.join(base_dir, 'models', f"{current_project.english_name}_task{task_id}")
    log_message(f'模型输出目录：{output_dir}', task_id=task_id)
    
    # 日志文件
    log_dir = os.path.join(base_dir, 'logs')
    log_file = os.path.join(log_dir, f'task_{task_id}.log')
    log_message(f'日志文件路径：{log_file}', task_id=task_id)
    
    # 训练脚本
    train_script = os.path.join(base_dir, 'scripts', 'train_model.py')
    log_message(f'训练脚本：{train_script}', task_id=task_id)
    
    # 权限检查
    log_message('开始权限检查...', task_id=task_id)
    try:
        # 检查日志目录是否可写
        if not os.path.exists(log_dir):
            log_message(f'创建日志目录：{log_dir}', task_id=task_id)
            os.makedirs(log_dir, exist_ok=True)
        
        # 测试日志文件是否可写
        test_file = os.path.join(log_dir, '.write_test')
        log_message('测试日志文件写入权限...', task_id=task_id)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('test')
        os.remove(test_file)
        log_message('日志目录权限检查通过', task_id=task_id)
        
        # 检查输出目录是否可写
        models_dir = os.path.join(base_dir, 'models')
        if not os.path.exists(models_dir):
            log_message(f'创建模型目录：{models_dir}', task_id=task_id)
            os.makedirs(models_dir, exist_ok=True)
        log_message('模型目录检查通过', task_id=task_id)
        
        # 检查训练脚本是否存在
        if not os.path.exists(train_script):
            error_msg = f'训练脚本不存在：{train_script}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            flash(error_msg, 'danger')
            storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
            return redirect(url_for('workspace.tasks', project_id=project_id))
        log_message(f'训练脚本存在：{train_script}', task_id=task_id)
        
        # 检查数据文件是否可读
        if not os.path.isfile(data_file_path):
            error_msg = f'数据文件不存在或不可读：{data_file_path}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            flash(error_msg, 'danger')
            storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
            return redirect(url_for('workspace.tasks', project_id=project_id))
        log_message(f'数据文件可访问：{data_file_path}', task_id=task_id)
        
        # 检查模型路径是否存在
        model_full_path = os.path.join(base_dir, model_path) if not os.path.isabs(model_path) else model_path
        if not os.path.exists(model_full_path):
            error_msg = f'基础模型不存在：{model_path}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            flash(error_msg, 'danger')
            storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
            return redirect(url_for('workspace.tasks', project_id=project_id))
        log_message(f'基础模型存在：{model_full_path}', task_id=task_id)
        
        log_message('所有权限检查通过', task_id=task_id)
        
    except PermissionError as e:
        error_msg = f'权限错误：{str(e)}。请确保 Web 应用有权限写入 logs 和 models 目录。'
        log_message(error_msg, 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
        storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
        return redirect(url_for('workspace.tasks', project_id=project_id))
    except Exception as e:
        error_msg = f'权限检查失败：{str(e)}'
        log_message(error_msg, 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
        storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    try:
        # 使用 subprocess 启动训练脚本，重定向输出到日志文件
        # 使用虚拟环境的 Python
        import sys
        import subprocess
        python_executable = sys.executable  # 使用当前运行环境的 Python
        
        # 检查是否需要拆分数据（如果 data_dir 是目录而不是文件路径）
        # 从 data_file_path 获取上传的数据文件
        data_file_path = data_files[0].get('file_path')
        
        # 创建临时数据目录（用于存放拆分后的文件）
        temp_data_dir = os.path.join(base_dir, 'data', f'{current_project.english_name}_temp_{task_id}')
        
        # 先拆分数据
        log_message(f'开始拆分数据集：{data_file_path}', task_id=task_id)
        split_script = os.path.join(base_dir, 'scripts', 'split_dataset.py')
        
        split_cmd = [
            python_executable, split_script,
            '--input_file', data_file_path,
            '--output_dir', temp_data_dir
        ]
        
        log_message(f'执行数据拆分...', task_id=task_id)
        result = subprocess.run(split_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f'数据拆分失败：{result.stderr}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            flash(error_msg, 'danger')
            storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
            return redirect(url_for('workspace.tasks', project_id=project_id))
        
        log_message(f'数据集拆分完成：{temp_data_dir}', task_id=task_id)
        
        # 使用拆分后的临时数据目录
        data_dir = temp_data_dir
        
        # 构建命令
        cmd = [
            python_executable, train_script,
            '--data_dir', data_dir,
            '--output_dir', output_dir,
            '--base_model', model_path,
            '--use_gpu', use_gpu,
            '--task_id', str(task_id)
        ]
        
        # 只在需要时添加 merge_model 参数
        if merge_model:
            cmd.append('--merge_model')
        
        log_message('准备启动训练进程...', task_id=task_id)
        log_message(f'Python 解释器：{python_executable}', task_id=task_id)
        log_message(f'命令：{" ".join(cmd)}', task_id=task_id)
        
        # 训练脚本的输出重定向到单独的文件（避免编码冲突）
        train_log_file = os.path.join(log_dir, f'task_{task_id}_train.log')
        log_message(f'训练日志文件：{train_log_file}', task_id=task_id)
        log_f = open(train_log_file, 'w', encoding='utf-8')
        
        # 后台运行（不等待完成）
        # 使用 CREATE_NEW_PROCESS_GROUP 确保子进程独立运行
        import subprocess
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        
        process = subprocess.Popen(cmd, cwd=base_dir, 
                                 stdout=log_f, stderr=log_f,
                                 close_fds=False,
                                 creationflags=creationflags)
        log_message(f'训练进程已启动，PID: {process.pid}', task_id=task_id)
        
        # 等待 2 秒检查进程是否立即失败
        import time
        time.sleep(2)
        if process.poll() is not None:
            # 进程已退出，说明启动失败
            returncode = process.returncode
            error_msg = f'训练进程启动失败，退出码：{returncode}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            storage.update('tasks', task_id, {
                'status': 'failed',
                'error': error_msg,
                'progress': 0
            })
            flash(error_msg, 'danger')
        else:
            # 进程正常运行，保存 PID 到任务记录
            storage.update('tasks', task_id, {
                'process_id': process.pid,
                'started_at': datetime.now().isoformat()
            })
            flash(f'训练任务已启动，系统日志：{log_file}，训练日志：{train_log_file}', 'success')
    except PermissionError as e:
        error_msg = f'权限错误：{str(e)}。请确保有权限执行训练脚本和写入输出目录。'
        log_message(error_msg, 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
        storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
    except Exception as e:
        error_msg = f'启动训练失败：{str(e)}'
        log_message(error_msg, 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
        storage.update('tasks', task_id, {'status': 'failed', 'error': error_msg})
    
    return redirect(url_for('workspace.tasks', project_id=project_id))

@bp.route('/<int:project_id>/tasks/<int:task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(project_id, task_id):
    """取消任务（项目空间内）"""
    from web.projects import Project
    import signal
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    task = tasks[0]
    if task['status'] in ['pending', 'running']:
        # 如果有进程 ID，尝试终止进程
        if task.get('process_id'):
            try:
                os.kill(task['process_id'], signal.SIGTERM)
                log_message(f'已终止任务 {task_id} 的进程，PID: {task["process_id"]}', task_id=task_id)
            except Exception as e:
                log_message(f'终止进程失败：{str(e)}', 'ERROR', task_id=task_id)
        
        storage.update('tasks', task_id, {'status': 'cancelled'})
        flash('任务已取消', 'success')
    else:
        flash('任务无法取消', 'warning')
    
    return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))


@bp.route('/<int:project_id>/gpu/check', methods=['GET'])
@login_required
def check_gpu_status(project_id):
    """检测 GPU 状态"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    # 运行检测脚本，设置 UTF-8 编码环境变量
    import subprocess
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(
        ['python', 'scripts/check_gpu.py'],
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        capture_output=True,
        text=True,
        env=env
    )
    
    return render_template('workspace/gpu_check.html', 
                         output=result.stdout,
                         current_project=current_project)


@bp.route('/<int:project_id>/gpu/install', methods=['GET'])
@login_required
def install_gpu_torch(project_id):
    """安装 GPU 版本的 PyTorch"""
    from web.projects import Project
    import sys
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    # 运行安装脚本
    import subprocess
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # 使用后台进程安装，设置环境变量以使用 UTF-8 编码
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    cmd = [
        sys.executable, 'scripts/install_torch.py'
    ]
    
    # 启动安装进程（不等待完成）
    subprocess.Popen(cmd, cwd=base_dir, env=env)
    
    flash('正在后台安装 GPU 版本 PyTorch，请查看控制台输出', 'info')
    return redirect(url_for('workspace.check_gpu_status', project_id=project_id))


@bp.route('/<int:project_id>/tasks/<int:task_id>/merge', methods=['GET'])
@login_required
def merge_task_model(project_id, task_id):
    """合并任务的 LoRA 模型到基础模型"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('workspace.tasks', project_id=project_id))
    
    task = tasks[0]
    log_message(f'开始合并模型操作：task_id={task_id}', task_id=task_id)
    
    if task['status'] != 'completed':
        log_message(f'任务状态不是 completed，当前状态：{task["status"]}', 'WARNING', task_id=task_id)
        flash('任务未完成，无法合并模型', 'warning')
        return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))
    
    try:
        # 运行合并脚本
        import subprocess
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        log_message(f'项目根目录：{base_dir}', task_id=task_id)
        
        output_dir = os.path.join(base_dir, 'models', f"{current_project.english_name}_task{task_id}")
        base_model = task.get('base_model')
        
        log_message(f'输出目录：{output_dir}', task_id=task_id)
        log_message(f'基础模型：{base_model}', task_id=task_id)
        
        if not base_model:
            log_message('任务没有基础模型信息，无法合并', 'ERROR', task_id=task_id)
            flash('任务没有基础模型信息，无法合并', 'danger')
            return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))
        
        # 检查输出目录是否存在
        if not os.path.exists(output_dir):
            error_msg = f'模型输出目录不存在：{output_dir}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            flash(error_msg, 'danger')
            return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))
        
        log_message(f'模型输出目录存在：{output_dir}', task_id=task_id)
        
        # 检查合并脚本是否存在
        merge_script = os.path.join(base_dir, 'scripts', 'merge_lora.py')
        if not os.path.exists(merge_script):
            error_msg = f'合并脚本不存在：{merge_script}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            flash(error_msg, 'danger')
            return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))
        
        log_message(f'合并脚本存在：{merge_script}', task_id=task_id)
        
        # 构建合并命令
        cmd = [
            sys.executable,
            merge_script,
            '--base_model', base_model,
            '--adapter_path', output_dir,
            '--output_dir', f"{output_dir}_merged"
        ]
        
        log_message(f'Python 解释器：{sys.executable}', task_id=task_id)
        log_message(f'合并命令：{" ".join(cmd)}', task_id=task_id)
        
        # 同步执行合并（需要等待完成）
        log_message(f'开始合并模型：{task_id}', task_id=task_id)
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        log_message(f'合并进程退出码：{result.returncode}', task_id=task_id)
        if result.stdout:
            log_message(f'合并输出：{result.stdout}', task_id=task_id)
        if result.stderr:
            log_message(f'合并错误输出：{result.stderr}', 'WARNING', task_id=task_id)
        
        if result.returncode == 0:
            # 合并成功
            log_message(f'模型合并成功：{task_id}', task_id=task_id)
            
            # 更新任务状态，标记已合并模型
            storage.update('tasks', task_id, {'merge_model': True})
            log_message(f'任务状态已更新：merge_model=True', task_id=task_id)
            
            flash('模型合并成功！完整模型已保存到 models 目录', 'success')
        else:
            # 合并失败
            error_msg = f'合并失败：{result.stderr}'
            log_message(error_msg, 'ERROR', task_id=task_id)
            flash(error_msg, 'danger')
        
    except Exception as e:
        error_msg = f'合并模型出错：{str(e)}'
        log_message(error_msg, 'ERROR', task_id=task_id)
        import traceback
        log_message(f'详细错误：{traceback.format_exc()}', 'ERROR', task_id=task_id)
        flash(error_msg, 'danger')
    
    return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))


@bp.route('/<int:project_id>/tasks/<int:task_id>/check', methods=['GET'])
@login_required
def check_task_status(project_id, task_id):
    """检查任务状态（用于轮询更新）"""
    from web.projects import Project
    import psutil
    
    current_project = Project.get(project_id)
    if not current_project:
        return {'error': '项目不存在'}, 404
    
    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        return {'error': '任务不存在'}, 404
    
    task = tasks[0]
    
    # 如果是运行状态，检查进程是否还在运行
    if task['status'] == 'running' and task.get('process_id'):
        try:
            process = psutil.Process(task['process_id'])
            if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                # 进程已结束，但任务状态还是 running，说明异常退出
                print(f'[ERROR] 任务 {task_id} 的进程已异常退出')
                storage.update('tasks', task_id, {
                    'status': 'failed',
                    'error': '训练进程异常退出，请查看日志文件',
                    'progress': task.get('progress', 0)
                })
                task['status'] = 'failed'
        except psutil.NoSuchProcess:
            # 进程不存在
            print(f'[ERROR] 任务 {task_id} 的进程不存在')
            storage.update('tasks', task_id, {
                'status': 'failed',
                'error': '训练进程不存在，请查看日志文件',
                'progress': task.get('progress', 0)
            })
            task['status'] = 'failed'
        except Exception as e:
            print(f'[ERROR] 检查进程状态失败：{str(e)}')
    
    return {
        'task_id': task['_id'],
        'status': task['status'],
        'progress': task.get('progress', 0),
        'error': task.get('error'),
        'name': task['name']
    }

@bp.route('/<int:project_id>/models/<int:model_id>')
@login_required
def model_detail(project_id, model_id):
    """模型详情（项目空间内）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    models = storage.find('models', {'_id': model_id})
    if not models:
        flash('模型不存在', 'danger')
        return redirect(url_for('workspace.models', project_id=project_id))
    
    model = models[0]
    return render_template('workspace/models/detail.html',
                         model=model,
                         current_project=current_project)

@bp.route('/<int:project_id>/models/<int:model_id>/delete', methods=['POST'])
@login_required
def delete_model(project_id, model_id):
    """删除模型（项目空间内）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))
    
    models = storage.find('models', {'_id': model_id})
    if not models:
        flash('模型不存在', 'danger')
        return redirect(url_for('workspace.models', project_id=project_id))
    
    model = models[0]
    model_path = model.get('file_path')
    
    # 删除文件
    if model_path and os.path.exists(model_path):
        os.remove(model_path)
    
    # 删除记录
    storage.delete('models', model_id)
    flash('模型已删除', 'success')
    return redirect(url_for('workspace.models', project_id=project_id))


@bp.route('/<int:project_id>/tasks/<int:task_id>/compare')
@login_required
def compare_models(project_id, task_id):
    """模型对比测试页面"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return redirect(url_for('projects.portal'))

    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        flash('任务不存在', 'danger')
        return redirect(url_for('workspace.tasks', project_id=project_id))

    task = tasks[0]
    log_message(f'访问模型对比页面：task_id={task_id}', task_id=task_id)

    # 任务必须已完成
    if task['status'] != 'completed':
        flash('任务未完成，无法进行对比测试', 'warning')
        return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))

    # 获取基础模型路径
    base_model = task.get('base_model')
    if not base_model:
        flash('任务没有基础模型信息，无法对比', 'danger')
        return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))

    # 获取合并后的模型路径
    merged_model_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'models',
        f"{current_project.english_name}_task{task_id}_merged"
    )

    # 检查合并模型是否存在
    merged_model_exists = os.path.exists(merged_model_dir)
    if not merged_model_exists:
        log_message(f'合并模型目录不存在：{merged_model_dir}', 'WARNING', task_id=task_id)
        flash('合并模型不存在，请先合并模型', 'warning')
        return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))

    # 检查基础模型路径是否有效
    base_model_path = base_model
    if not os.path.isabs(base_model):
        base_model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            base_model
        )

    if not os.path.exists(base_model_path):
        log_message(f'基础模型路径不存在：{base_model_path}', 'ERROR', task_id=task_id)
        flash(f'基础模型路径不存在：{base_model}', 'danger')
        return redirect(url_for('workspace.task_detail', project_id=project_id, task_id=task_id))

    # 获取设备信息
    from web.services.model_cache import model_cache
    device_info = model_cache.get_device_info()

    log_message(f'对比页面加载完成：base={base_model_path}, merged={merged_model_dir}', task_id=task_id)

    return render_template(
        'workspace/tasks/compare.html',
        current_project=current_project,
        task=task,
        base_model_path=base_model_path,
        merged_model_path=merged_model_dir,
        device_info=device_info,
    )


@bp.route('/<int:project_id>/tasks/<int:task_id>/compare/generate', methods=['POST'])
@login_required
def compare_generate(project_id, task_id):
    """模型对比推理 API"""
    from web.projects import Project
    import json as json_module

    current_project = Project.get(project_id)
    if not current_project:
        return {'error': '项目不存在'}, 404

    tasks = storage.find('tasks', {'_id': task_id})
    if not tasks:
        return {'error': '任务不存在'}, 404

    task = tasks[0]

    # 解析请求参数
    data = request.get_json()
    if not data or 'prompt' not in data:
        return {'error': '缺少 prompt 参数'}, 400

    prompt = data['prompt'].strip()
    if not prompt:
        return {'error': 'prompt 不能为空'}, 400

    # 可选参数
    max_new_tokens = data.get('max_new_tokens', 512)
    temperature = data.get('temperature', 0.7)
    model_type = data.get('model_type', 'both')  # 'base', 'merged', 'both'
    enable_thinking = data.get('enable_thinking', False)

    log_message(
        f'对比推理请求：task_id={task_id}, prompt长度={len(prompt)}, '
        f'model_type={model_type}, max_tokens={max_new_tokens}, temp={temperature}, '
        f'thinking={enable_thinking}',
        task_id=task_id
    )

    # 获取模型路径
    base_model = task.get('base_model')
    if not base_model:
        return {'error': '任务没有基础模型信息'}, 400

    base_model_path = base_model
    if not os.path.isabs(base_model):
        base_model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            base_model
        )

    merged_model_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'models',
        f"{current_project.english_name}_task{task_id}_merged"
    )

    # 构造对话 prompt（使用 chat 格式）
    # Qwen3.5 思考模式：
    #   开启思考：assistant 后加 \n\n（模型先输出思考内容，再输出回答）
    #   关闭思考：assistant 后加 \n\n\n\n（模型先输出空思考块，再输出回答）
    if enable_thinking:
        chat_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n\n"
    else:
        chat_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n\n\n\n"

    result = {}

    try:
        from web.services.model_cache import model_cache

        # 推理 base 模型
        if model_type in ('base', 'both'):
            log_message(f'开始推理基础模型：{base_model_path}', task_id=task_id)
            try:
                base_response = model_cache.generate(
                    base_model_path,
                    chat_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                )
                # 解析思考内容
                # Qwen3.5 思考模式输出格式：思考内容\n\n\n\n正式回答
                base_thinking = None
                base_answer = base_response
                if enable_thinking and '\n\n\n\n' in base_response:
                    parts = base_response.split('\n\n\n\n', 1)
                    thinking_text = parts[0].strip()
                    if thinking_text:
                        base_thinking = thinking_text
                    base_answer = parts[1].strip() if len(parts) > 1 else base_response

                result['base_response'] = base_answer
                if base_thinking:
                    result['base_thinking'] = base_thinking
                log_message(f'基础模型推理完成，回复长度={len(base_response)}', task_id=task_id)
            except Exception as e:
                log_message(f'基础模型推理失败：{e}', 'ERROR', task_id=task_id)
                result['base_error'] = str(e)

        # 推理合并模型
        if model_type in ('merged', 'both'):
            log_message(f'开始推理合并模型：{merged_model_dir}', task_id=task_id)
            try:
                merged_response = model_cache.generate(
                    merged_model_dir,
                    chat_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                )
                # 解析思考内容
                # Qwen3.5 思考模式输出格式：思考内容\n\n\n\n正式回答
                merged_thinking = None
                merged_answer = merged_response
                if enable_thinking and '\n\n\n\n' in merged_response:
                    parts = merged_response.split('\n\n\n\n', 1)
                    thinking_text = parts[0].strip()
                    if thinking_text:
                        merged_thinking = thinking_text
                    merged_answer = parts[1].strip() if len(parts) > 1 else merged_response

                result['merged_response'] = merged_answer
                if merged_thinking:
                    result['merged_thinking'] = merged_thinking
                log_message(f'合并模型推理完成，回复长度={len(merged_response)}', task_id=task_id)
            except Exception as e:
                log_message(f'合并模型推理失败：{e}', 'ERROR', task_id=task_id)
                result['merged_error'] = str(e)

        # 附加设备信息
        result['device_info'] = model_cache.get_device_info()
        result['cached_models'] = model_cache.get_cached_models()

        # 保存对比历史记录
        try:
            history_record = {
                'task_id': task_id,
                'project_id': project_id,
                'prompt': prompt,
                'max_new_tokens': max_new_tokens,
                'temperature': temperature,
                'enable_thinking': enable_thinking,
                'base_response': result.get('base_response', ''),
                'base_thinking': result.get('base_thinking', ''),
                'base_error': result.get('base_error', ''),
                'merged_response': result.get('merged_response', ''),
                'merged_thinking': result.get('merged_thinking', ''),
                'merged_error': result.get('merged_error', ''),
                'created_at': datetime.now().isoformat(),
            }
            storage.insert('compare_history', history_record)
            # 把记录 ID 返回给前端
            result['history_id'] = history_record['_id']

            # 限制历史记录最多 20 条，超过删除最早的
            all_records = storage.find('compare_history', {'task_id': task_id})
            if len(all_records) > 20:
                # 按时间正序排序，删除最老的
                all_records.sort(key=lambda x: x.get('created_at', ''))
                excess = len(all_records) - 20
                for i in range(excess):
                    storage.delete('compare_history', all_records[i]['_id'])
                log_message(f'历史记录超过 20 条，已清理 {excess} 条', task_id=task_id)

            log_message(f'对比历史已保存，ID={history_record["_id"]}', task_id=task_id)
        except Exception as e:
            log_message(f'保存对比历史失败：{e}', 'WARNING', task_id=task_id)

        return result

    except Exception as e:
        log_message(f'对比推理异常：{e}', 'ERROR', task_id=task_id)
        import traceback
        log_message(f'详细错误：{traceback.format_exc()}', 'ERROR', task_id=task_id)
        return {'error': str(e)}, 500


@bp.route('/<int:project_id>/tasks/<int:task_id>/compare/device_info')
@login_required
def compare_device_info(project_id, task_id):
    """获取当前设备信息"""
    from web.services.model_cache import model_cache
    info = model_cache.get_device_info()
    info['cached_models'] = model_cache.get_cached_models()
    return info


@bp.route('/<int:project_id>/tasks/<int:task_id>/compare/history')
@login_required
def compare_history_list(project_id, task_id):
    """获取对比历史记录列表"""
    records = storage.find('compare_history', {'task_id': task_id})
    # 按时间倒序
    records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return {'records': records}


@bp.route('/<int:project_id>/tasks/<int:task_id>/compare/history/<int:history_id>/delete', methods=['POST'])
@login_required
def compare_history_delete(project_id, task_id, history_id):
    """删除对比历史记录"""
    log_message(f'删除对比历史记录：history_id={history_id}', task_id=task_id)
    records = storage.find('compare_history', {'_id': history_id})
    if not records:
        return {'error': '记录不存在'}, 404
    storage.delete('compare_history', history_id)
    log_message(f'对比历史记录已删除：history_id={history_id}', task_id=task_id)
    return {'success': True}


@bp.route('/<int:project_id>/tasks/<int:task_id>/training_metrics')
@login_required
def training_metrics(project_id, task_id):
    """获取训练指标（损失曲线数据）"""
    from web.projects import Project
    current_project = Project.get(project_id)
    if not current_project:
        return {'metrics': None}

    task_records = storage.find('tasks', {'_id': task_id})
    if not task_records:
        return {'error': '任务不存在'}, 404
    task = task_records[0]

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    output_dir = os.path.join(base_dir, 'models', f"{current_project.english_name}_task{task_id}")

    # trainer_state.json 可能在 output_dir 根目录或最新的 checkpoint 目录
    trainer_state_path = None
    if os.path.exists(os.path.join(output_dir, 'trainer_state.json')):
        trainer_state_path = os.path.join(output_dir, 'trainer_state.json')
    else:
        # 查找最新的 checkpoint
        checkpoints = sorted(glob.glob(os.path.join(output_dir, 'checkpoint-*')))
        if checkpoints:
            trainer_state_path = os.path.join(checkpoints[-1], 'trainer_state.json')

    if not trainer_state_path or not os.path.exists(trainer_state_path):
        log_message(f'trainer_state.json 不存在：output_dir={output_dir}', 'WARNING', task_id=task_id)
        return {'metrics': None}

    try:
        with open(trainer_state_path, 'r', encoding='utf-8') as f:
            trainer_state = json.load(f)

        log_history = trainer_state.get('log_history', [])
        log_message(f'找到 {len(log_history)} 条 log_history', 'INFO', task_id=task_id)
        if not log_history:
            return {'metrics': None}

        steps = []
        losses = []
        for entry in log_history:
            if 'eval_loss' in entry:
                steps.append(int(entry.get('step', 0)))
                losses.append(float(entry['eval_loss']))

        log_message(f'提取到 {len(steps)} 个 loss 数据', 'INFO', task_id=task_id)
        if not steps:
            return {'metrics': None}

        return {
            'metrics': {
                'steps': steps,
                'losses': losses,
                'epoch': trainer_state.get('epoch', 0),
                'num_train_epochs': trainer_state.get('num_train_epochs', 0),
                'train_batch_size': trainer_state.get('train_batch_size', 0),
            }
        }
    except Exception as e:
        log_message(f'读取训练指标失败：{e}', 'WARNING', task_id=task_id)
        return {'metrics': None}
