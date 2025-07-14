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
