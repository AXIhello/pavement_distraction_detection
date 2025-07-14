# 安全相关的工具函数（加密、JWT等）
import jwt
import datetime

SECRET_KEY = "your_secret_key"

def create_jwt_token(user):
    payload = {
        'user_id': user.id,
        'role': user.role,            # 加入角色字段
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

from functools import wraps
from flask import request, g, jsonify
from app.core.models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'msg': '缺少或无效的Token'}), 401
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user = User.query.get(payload['user_id'])
            if not user:
                return jsonify({'msg': '用户不存在'}), 401
            g.user = user  # 设置全局用户
        except jwt.ExpiredSignatureError:
            return jsonify({'msg': 'Token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'msg': '无效的Token'}), 401
        return f(*args, **kwargs)
    return decorated