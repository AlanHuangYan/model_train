from flask import render_template, redirect, url_for, flash, send_file
from flask_login import login_required
from web.models import bp
from web.storage import storage
import os


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
