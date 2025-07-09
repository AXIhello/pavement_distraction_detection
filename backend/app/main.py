# backend/app/main.py
from flask import Flask, request
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# 添加上级目录到 Python 路径中，以便导入其他模块
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入配置和日志设置
from app.app_config import DevelopmentConfig, ProductionConfig
from app.utils.logger import setup_logging, get_logger
from app.extensions import db
from app.core.models import User  # 确保模型在 db.create_all 前被导入

# 根据环境变量选择配置
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    config_class = ProductionConfig
else:
    config_class = DevelopmentConfig
app = Flask(__name__)
app.config.from_object(config_class)
CORS(app)    # 允许跨域请求

db.init_app(app)

# 初始化日志系统
setup_logging(app)
# 获取一个应用级别的日志器
app_logger = get_logger(__name__)

# 测试日志写入
app_logger.info("测试日志写入：如果你看到这条日志，说明日志文件写入正常！")

# 配置 Swagger UI
api = Api(app,
          version='1.0',
          title='综合管理平台 API',
          description='人脸识别、路面病害、交通分析及日志告警',
          doc='/doc',
          prefix='/api')

# 导入并注册 API 命名空间
from app.api.auth import ns as auth_ns
from app.api.face_recognition import ns as face_ns
from app.api.pavement_detection import ns as pavement_ns
from app.api.traffic_analysis import ns as traffic_ns
from app.api.logging_alerts import ns as logging_alerts_ns # 导入日志告警命名空间

api.add_namespace(auth_ns)
api.add_namespace(face_ns)
api.add_namespace(pavement_ns)
api.add_namespace(traffic_ns)
api.add_namespace(logging_alerts_ns) # 注册日志告警命名空间

# 示例：记录一些启动日志
app_logger.info("Flask 应用启动中...")
app_logger.debug(f"当前运行环境: {env}")

# 可以在其他地方使用 app.logger 或 get_logger() 来记录日志
@app.before_request
def log_request_info():
    app_logger.info(f"请求 {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response_info(response):
    app_logger.info(f"响应 {request.method} {request.path} with status {response.status_code}")
    return response

# ... 其他 Flask 路由或错误处理 ...

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("当前注册模型表：", db.metadata.tables.keys())
            app_logger.info("数据库连接成功，所有表已创建（或已存在）")
        except Exception as e:
            app_logger.error(f"数据库连接失败：{str(e)}", exc_info=True)
            raise
    app.run()   # app.run() # host和port可以在config中设置或直接写在这里
