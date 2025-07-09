# backend/app/main.py
from flask import Flask, request
from flask_restx import Api
import os
import json

# 导入配置和日志设置
from .app_config import DevelopmentConfig, ProductionConfig
from .utils.logger import setup_logging, get_logger
# 导入 Flask-SocketIO
from flask_socketio import SocketIO, emit

# 导入人脸识别服务
from .services.face_service import FaceRecognitionService

# 根据环境变量选择配置
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    config_class = ProductionConfig
else:
    config_class = DevelopmentConfig

app = Flask(__name__)
app.config.from_object(config_class)

# 初始化 SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化日志系统
setup_logging(app)
# 获取一个应用级别的日志器
app_logger = get_logger(__name__)

# --- 初始化人脸识别服务 ---
# 将 app.config 传递给服务，以便服务可以获取路径或其他配置
face_recognition_service = FaceRecognitionService(app.config)

# 在应用上下文启动时初始化 Dlib 模型和人脸数据库
# 确保在 WSGI 服务器启动前完成初始化
with app.app_context():
    try:
        face_recognition_service.initialize_models()
        app_logger.info("人脸识别服务初始化完成")
    except Exception as e:
        app_logger.error(f"人脸识别服务初始化失败: {e}", exc_info=True)

# 测试日志写入
app_logger.info("测试日志写入：如果你看到这条日志，说明日志文件写入正常！")

# 配置 Swagger UI
api = Api(app,
          version='1.0',
          title='综合管理平台 API',
          description='人脸识别、路面病害、交通分析及日志告警',
          doc='/doc')

# 导入并注册 API 命名空间
from .api.auth import ns as auth_ns
from .api.face_recognition import ns as face_ns
from .api.pavement_detection import ns as pavement_ns
from .api.traffic_analysis import ns as traffic_ns
from .api.logging_alerts import ns as logging_alerts_ns  # 导入日志告警命名空间

api.add_namespace(auth_ns)
api.add_namespace(face_ns)
api.add_namespace(pavement_ns)
api.add_namespace(traffic_ns)
api.add_namespace(logging_alerts_ns)  # 注册日志告警命名空间


# --- SocketIO 事件处理 ---
@socketio.on('connect')
def handle_connect():
    app_logger.info("SocketIO 客户端连接")
    emit('connected', {'status': 'connected', 'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    app_logger.info("SocketIO 客户端断开连接")

@socketio.on('test')
def handle_test(data):
    app_logger.info(f"收到测试消息: {data}")
    emit('test_response', {'status': 'test', 'message': '测试成功'})

@socketio.on('face_recognition')
def handle_face_recognition(data):
    app_logger.info("收到人脸识别请求")
    try:
        base64_image = data.get('image', '')
        if not base64_image:
            emit('face_result', {'success': False, 'message': '没有图像数据'})
            return

        # 调用人脸识别服务进行处理
        recognition_results = face_recognition_service.recognize_face(base64_image)

        # 判断识别结果，统一返回格式
        if (
                isinstance(recognition_results, list)
                and recognition_results
                and recognition_results[0].get("name") != "未检测到人脸"
                and recognition_results[0].get("status") != "error"
        ):
            emit('face_result', {
                "success": True,
                "faces": recognition_results
            })
        elif (
                isinstance(recognition_results, list)
                and recognition_results
                and recognition_results[0].get("status") == "error"
        ):
            emit('face_result', {
                "success": False,
                "message": recognition_results[0].get("message", "识别出错")
            })
        else:
            emit('face_result', {
                "success": False,
                "message": "未检测到人脸"
            })

    except Exception as e:
        app_logger.error(f"人脸识别处理错误: {e}", exc_info=True)
        emit('face_result', {"success": False, "message": str(e)})


# 示例：记录一些启动日志
app_logger.info("Flask 应用启动中...")
app_logger.debug(f"当前运行环境: {env}")


# --- Flask 路由和错误处理保持不变 ---
@app.before_request
def log_request_info():
    if not request.path.startswith('/ws/'):  # 排除 WebSocket 请求的日志
        app_logger.info(f"请求 {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def log_response_info(response):
    if not request.path.startswith('/ws/'):  # 排除 WebSocket 请求的日志
        app_logger.info(f"响应 {request.method} {request.path} with status {response.status_code}")
    return response


# --- 运行 Flask 应用 (使用 SocketIO) ---
if __name__ == '__main__':
    app_logger.info("Flask 应用启动中...")
    app_logger.debug(f"当前运行环境: {env}")

    # 使用 SocketIO 启动服务器
    socketio.run(app, host='127.0.0.1', port=8000, debug=True)