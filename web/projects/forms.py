from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
from web.projects import Project

class ProjectForm(FlaskForm):
    """项目表单"""
    name = StringField('项目名称', validators=[
        DataRequired(message='请输入项目名称'),
        Length(min=2, max=100, message='项目名称长度必须在 2-100 个字符之间')
    ])
    english_name = StringField('英文名称', validators=[
        DataRequired(message='请输入英文名称'),
        Length(min=2, max=50, message='英文名称长度必须在 2-50 个字符之间'),
        Regexp(r'^[a-zA-Z][a-zA-Z0-9_-]*$', message='英文名称只能包含字母、数字、下划线和连字符，且必须以字母开头')
    ])
    description = TextAreaField('项目描述', validators=[
        Length(max=500, message='项目描述不能超过 500 个字符')
    ])
    submit = SubmitField('提交')
    
    def validate_english_name(self, field):
        """检查英文名称是否已存在"""
        existing = Project.find_by_english_name(field.data)
        if existing:
            raise ValidationError('该英文名称已被使用，请使用其他名称')
    
    @staticmethod
    def find_by_english_name(english_name):
        """根据英文名称查找项目"""
        from web.storage import storage
        if not storage:
            return None
        projects = storage.find('projects', {'english_name': english_name})
        return projects[0] if projects else None
