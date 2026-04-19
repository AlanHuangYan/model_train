from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from web.auth.forms import LoginForm, RegistrationForm
from web.auth import User, bp
from web.storage import storage


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        flash('邮箱或密码错误', 'danger')
    
    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        User.create(form.email.data, form.password.data)
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已登出', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/users')
@login_required
def list_users():
    """用户列表（分页）"""
    page = request.args.get('page', 1, type=int)
    users, current_page, total_pages = User.get_all(page=page, per_page=10)
    return render_template('auth/user_list.html', 
                         users=users, 
                         current_page=current_page, 
                         total_pages=total_pages)


@bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """删除用户（不能删除自己）"""
    if user_id == current_user.id:
        flash('不能删除自己', 'warning')
        return redirect(url_for('auth.list_users'))
    
    if User.delete(user_id):
        flash('用户已删除', 'success')
    else:
        flash('删除失败', 'danger')
    
    return redirect(url_for('auth.list_users'))
