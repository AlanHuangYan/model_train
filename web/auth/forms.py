from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from flask import current_app


class LoginForm(FlaskForm):
    """登录表单"""
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    """注册表单"""
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(), EqualTo('password', message='两次密码必须一致')
    ])
    submit = SubmitField('注册')
    
    def validate_email(self, field):
        """验证邮箱是否已存在"""
        from web.storage import storage
        if storage:
            users = storage.find('users', {'email': field.data})
            if users:
                raise ValidationError('该邮箱已被注册')
