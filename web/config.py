import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF token 永不过期（简化使用）
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 存储文件路径
    STORAGE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage')
    
    # 模型存储路径
    MODEL_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
