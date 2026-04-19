from flask import render_template
from flask_login import login_required
from web.dashboard import bp
from web.storage import storage


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
