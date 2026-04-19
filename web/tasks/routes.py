from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from web.tasks import bp
from web.storage import storage
from datetime import datetime


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
