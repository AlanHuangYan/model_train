from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from web.data import bp
from web.storage import storage
import os
import pandas as pd

ALLOWED_EXTENSIONS = {'csv', 'json'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
@login_required
def list_data():
    """数据文件列表"""
    data_files = storage.load('data_files')
    data_files = sorted(data_files, key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('data/list.html', data_files=data_files)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_data():
    """上传数据文件"""
    if request.method == 'POST':
        name = request.form.get('name')
        
        if 'file' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(url_for('data.upload_data'))
        
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(url_for('data.upload_data'))
        
        if not name:
            flash('数据名称不能为空', 'danger')
            return redirect(url_for('data.upload_data'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # 记录到存储
            data_file = {
                'name': name,
                'filename': filename,
                'file_path': file_path,
                'uploaded_by': current_user.email,
                'size': os.path.getsize(file_path)
            }
            
            # 如果是 CSV，尝试读取基本信息
            if filename.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path, nrows=5)
                    data_file['preview'] = df.to_html(classes='table table-sm', index=False)
                    data_file['rows'] = len(pd.read_csv(file_path))
                    data_file['columns'] = list(df.columns)
                except Exception as e:
                    flash(f'无法解析 CSV 文件：{str(e)}', 'warning')
            
            storage.insert('data_files', data_file)
            flash('文件上传成功', 'success')
            return redirect(url_for('data.list_data'))
        else:
            flash('不支持的文件格式，请上传 CSV 或 JSON 文件', 'danger')
    
    return render_template('data/upload.html')


@bp.route('/<int:file_id>')
@login_required
def data_detail(file_id):
    """数据文件详情"""
    data_files = storage.find('data_files', {'_id': file_id})
    if not data_files:
        flash('文件不存在', 'danger')
        return redirect(url_for('data.list_data'))
    
    data_file = data_files[0]
    return render_template('data/detail.html', data_file=data_file)


@bp.route('/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_data(file_id):
    """删除数据文件"""
    data_files = storage.find('data_files', {'_id': file_id})
    if not data_files:
        flash('文件不存在', 'danger')
        return redirect(url_for('data.list_data'))
    
    data_file = data_files[0]
    file_path = data_file.get('file_path')
    
    # 删除文件
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # 删除记录
    storage.delete('data_files', file_id)
    flash('文件已删除', 'success')
    return redirect(url_for('data.list_data'))
