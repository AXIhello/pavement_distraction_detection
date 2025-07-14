# backend/app/main.py
from flask import Flask, request, g
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

import os
import json

# 添加上级目录到 Python 路径中，以便导入其他模块
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入配置和日志设置
from app.app_config import DevelopmentConfig, ProductionConfig
from app.utils.logger import setup_logging, get_logger
from app.extensions import db
from app.core.models import User  # 确保模型在 db.create_all 前被导入

# 导入 Flask-SocketIO
from flask_socketio import SocketIO, emit

# 导入人脸识别服务
from .services.face_service import FaceRecognitionService

# 导入告警模块
from .services.alert_service import create_alert_video, save_alert_frame, update_alert_video_frame_count

# 导入JWT相关
import jwt
from .core.security import SECRET_KEY

from app.services.liveness_service import liveness_check
# 根据环境变量选择配置
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    config_class = ProductionConfig
else:
    config_class = DevelopmentConfig

app = Flask(__name__)
app.config.from_object(config_class)
CORS(app)  # 允许跨域请求

db.init_app(app)

# 初始化 SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化日志系统
setup_logging(app)
# 获取一个应用级别的日志器
app_logger = get_logger(__name__)

# --- 初始化人脸识别服务 ---
# 将 app.config 传递给服务，以便服务可以获取路径或其他配置
face_recognition_service = FaceRecognitionService(app.config)

# 将服务设置为Flask应用的属性，以便在其他模块中访问
app.face_recognition_service = face_recognition_service

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
          doc='/doc',
          prefix='/api')

# 导入并注册 API 命名空间
from .api.auth import ns as auth_ns
from .api.face_recognition import ns as face_ns
from .api.pavement_detection import ns as pavement_ns, get_pavement_socketio_handlers
from .api.traffic_analysis import ns as traffic_ns
from .api.logging_alerts import ns as logging_alerts_ns  # 导入日志告警命名空间

api.add_namespace(auth_ns)
api.add_namespace(face_ns)
api.add_namespace(pavement_ns)
api.add_namespace(traffic_ns)
api.add_namespace(logging_alerts_ns)  # 注册日志告警命名空间

# 获取路面检测的Socket.IO处理器
pavement_handlers = get_pavement_socketio_handlers()


# --- SocketIO 事件处理 ---
@socketio.on('connect')
def handle_connect():
    # app_logger.info("SocketIO 客户端连接")
    sid = request.sid
    app_logger.info(f"SocketIO 客户端连接: {sid}")
    client_recognition_status[sid] = True  # 新连接默认允许识别


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    app_logger.info(f"SocketIO 客户端断开连接: {sid}")
    client_recognition_status.pop(sid, None)  # 断开时清理状态


import time
from collections import defaultdict, deque

recent_results = defaultdict(lambda: deque())
first_frame_processed = defaultdict(lambda: False)  # 用于标记每个客户端的首帧是否已处理
video_id_map = {}


@socketio.on('face_recognition')
def handle_face_recognition(data):
    from flask import request
    # 处理前端通过SocketIO发送过来的人脸识别请求
    from flask import  request
    from datetime import datetime
    from pathlib import Path
    sid = request.sid
    # 判断该客户端是否允许继续识别
    if not client_recognition_status.get(sid, True):
        # 已标记停止识别，忽略该客户端请求
        app_logger.info(f"忽略客户端 {sid} 的识别请求，因为已收到结束信号")
        return

    # 首帧处理逻辑（如初始化告警模块、记录日志、写数据库等）
    if not first_frame_processed[sid]:
        app_logger.info(f"首次接收到人脸图像，sid={sid}")
        first_frame_processed[sid] = True
        # 自动生成保存路径
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        save_dir = Path(f'data/alert_videos/face/video_{timestamp}')
        save_dir.mkdir(parents=True, exist_ok=True)
        # 创建人脸告警视频记录
        video_id = create_alert_video('face', f'video_{timestamp}', str(save_dir), 0, 0, user_id=None)
        video_id_map[sid] = video_id  # 保存视频ID到映射中

    app_logger.info("收到人脸识别请求")
    try:
        base64_image = data.get('image', '')
        req_id = data.get('req_id')  # 获取前端发送的 req_id
        if not base64_image:
            # 没有图像数据，直接返回错误
            emit('face_result', {'success': False, 'message': '没有图像数据', 'req_id': req_id})
            return
        # 调用人脸识别服务进行处理
        recognition_results = face_recognition_service.recognize_face(base64_image)
        if not recognition_results or not isinstance(recognition_results,list):
            # 识别结果异常，直接返回
            emit('face_result', {'success': False, 'message': '识别失败', 'req_id': req_id})
            return

        # 立即向前端发送bbox信息（用于画框）
        bboxes = [
            face["bbox"]
            for face in recognition_results
            if "bbox" in face
        ]
        if bboxes:
            app_logger.info(f"检测到人脸框，已发送bbox详细信息={bboxes}")
            emit('face_bbox',{
                "success": True,
                "bboxes": bboxes,
                "req_id": req_id
            })
        # 直接返回本帧识别结果给前端（不再做三帧一致判定，交由前端处理）
        emit('face_result', {
            "success": True,
            "faces": recognition_results,
            "req_id": req_id
        })
    except Exception as e:
        app_logger.error(f"人脸识别处理错误: {e}", exc_info=True)
        emit('face_result', {"success": False, "message": str(e), 'req_id': data.get('req_id')})


# 处理人脸识别结束信号
from flask import request

# 维护一个字典，存储每个客户端（sid）是否继续允许识别，True=允许识别，False=停止识别
client_recognition_status = {}


@socketio.on('face_recognition_end')
def handle_face_recognition_end(data):
    sid = request.sid
    app_logger.info(f"收到客户端 {sid} 的识别结束信号: {data}")
    client_recognition_status[sid] = False  # 标记该客户端停止识别


# --- 路面检测 Socket.IO 事件处理 ---
@socketio.on('video_frame')
def handle_video_frame(data):
    """处理路面检测视频帧"""
    app_logger.info("收到路面检测视频帧")
    pavement_handlers['video_frame'](data)


@socketio.on('video_stream_end')
def handle_video_stream_end(data):
    """处理视频流结束"""
    app_logger.info("收到视频流结束信号")
    pavement_handlers['video_stream_end'](data)


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


@app.before_request
def load_user_from_token():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = User.query.get(user_id)
            if user:
                g.user = {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                }
            else:
                g.user = None
        except jwt.ExpiredSignatureError:
            app_logger.warning("JWT过期")
            g.user = None
        except jwt.InvalidTokenError:
            app_logger.warning("JWT无效")
            g.user = None
    else:
        g.user = None
liveness_status = {}

@socketio.on('liveness_detection')
def handle_liveness_detection(data):
    from flask import request
    sid = request.sid
    base64_image = data.get('image', '')
    if not base64_image:
        emit('liveness_result', {'success': False, 'message': '没有图像数据'})
        return

    progress, next_action, status_dict = liveness_check(base64_image, liveness_status.get(sid, {}))
    liveness_status[sid] = status_dict

    emit('liveness_result', {
        'success': True,
        'progress': progress,
        'next_action': next_action,
        'status': status_dict
    })

    if progress == 100:
        liveness_status.pop(sid, None)

# --- 运行 Flask 应用 (使用 SocketIO) ---
if __name__ == '__main__':
    with app.app_context():
        try:
            #db.drop_all()  # 清空数据库（仅在开发环境中使用）
            db.create_all()
            print("当前注册模型表：", db.metadata.tables.keys())
            app_logger.info("数据库连接成功，所有表已创建（或已存在）")
        except Exception as e:
            app_logger.error(f"数据库连接失败：{str(e)}", exc_info=True)
            raise
    #app.run()   # app.run() # host和port可以在config中设置或直接写在这里
    app_logger.info("Flask 应用启动中...")
    app_logger.debug(f"当前运行环境: {env}")

    # 使用 SocketIO 启动服务器
    socketio.run(app, host='127.0.0.1', port=8000, debug=False)

    from flask import request, g, jsonify, current_app
    import jwt


    @app.before_request
    def load_user_from_token():
        auth_header = request.headers.get('Authorization', None)
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                try:
                    # 用你自己的密钥和算法解码
                    payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                    # 假设token里有 user_id 字段
                    g.user_id = payload.get('user_id')
                except jwt.ExpiredSignatureError:
                    return jsonify({'success': False, 'message': 'Token已过期'}), 401
                except jwt.InvalidTokenError:
                    return jsonify({'success': False, 'message': '无效的Token'}), 401
            else:
                g.user_id = None
        else:
            g.user_id = None
