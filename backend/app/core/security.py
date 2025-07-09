# 安全相关的工具函数（加密、JWT等）
import jwt
import datetime

SECRET_KEY = "your_secret_key"

def create_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
