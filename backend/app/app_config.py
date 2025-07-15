import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key'
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123@localhost:3306/test_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮件验证码发送邮箱配置
    SMTP_CONFIG = {
    "server": "smtp.qq.com",
    "port": 465,
    "from_email": "2330881321@qq.com",
    "auth_code": "skhkuriqzfqkeccb"
}

    # ... 其他配置 ...

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO') # 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs') # 日志文件存放目录

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'INFO'
    # ... 生产环境特有配置 ...