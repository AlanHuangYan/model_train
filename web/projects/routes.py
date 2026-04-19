from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from web.projects import bp, Project, forms
import os

@bp.route('/')
@login_required
def portal():
    """项目门户 - 显示所有项目"""
    projects = Project.get_all()
    
    # 获取每个项目的资源数量
    from web.storage import storage
    for project in projects:
        project.task_count = len(storage.find('tasks', {'project_id': project.id}))
        project.model_count = len(storage.find('models', {'project_id': project.id}))
        project.data_count = len(storage.find('data_files', {'project_id': project.id}))
    
    return render_template('projects/portal.html', projects=projects)

@bp.route('/<int:project_id>/workspace')
@login_required
def project_workspace(project_id):
    """项目空间 - 进入特定项目"""
    project = Project.get(project_id)
    if not project:
        flash('项目不存在', 'danger')
        return redirect(url_for('projects.portal'))
    
    # 设置当前项目到 session
    session['current_project_id'] = project_id
    session['current_project_name'] = project.name
    
    # 重定向到项目空间仪表盘
    return redirect(url_for('workspace.dashboard', project_id=project_id))

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """创建项目"""
    form = forms.ProjectForm()
    if form.validate_on_submit():
        project_id = Project.create(
            name=form.name.data,
            english_name=form.english_name.data,
            description=form.description.data,
            created_by=current_user.email
        )
        
        if project_id:
            flash('项目创建成功', 'success')
            return redirect(url_for('projects.portal'))
        else:
            flash('创建项目失败，英文名称可能已存在', 'danger')
    
    return render_template('projects/create.html', form=form)

@bp.route('/<int:project_id>')
@login_required
def project_detail(project_id):
    """项目详情"""
    project = Project.get(project_id)
    if not project:
        flash('项目不存在', 'danger')
        return redirect(url_for('projects.portal'))
    
    # 获取项目相关的任务、模型、数据
    from web.storage import storage
    tasks = storage.find('tasks', {'project_id': project_id})
    models = storage.find('models', {'project_id': project_id})
    data_files = storage.find('data_files', {'project_id': project_id})
    
    return render_template('projects/detail.html', 
                         project=project, 
                         tasks=tasks, 
                         models=models, 
                         data_files=data_files)

@bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """删除项目"""
    if Project.delete(project_id):
        flash('项目已删除', 'success')
    else:
        flash('删除项目失败', 'danger')
    
    return redirect(url_for('projects.portal'))
