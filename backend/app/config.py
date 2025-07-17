# backend/app/config.py
import os

class Config:
    """基础配置类"""
    # Django后端配置 - 直接指定IP地址
    DJANGO_BASE_URL = 'http://10.61.169.63:9000'
    
    # Flask应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/mydb?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 网络配置 - 允许跨域访问
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 开发环境Django地址
    DJANGO_BASE_URL = 'http://10.61.169.63:9000'
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境Django地址
    DJANGO_BASE_URL = 'http://10.61.169.63:9000'
    
    # 生产环境安全配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',') 