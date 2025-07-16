# 认证相关接口
from flask_restx import Namespace, Resource, fields,marshal
from ..core.models import User, find_user_by_username, find_user_by_email, create_user
from ..core.security import create_jwt_token
from flask import current_app, Blueprint, request, jsonify, g, session, send_file, make_response
from ..utils.email_service import send_email_code, verify_email_code
from functools import wraps
from ..extensions import db
import random, string, io
from captcha.image import ImageCaptcha
from ..utils.logger import get_logger
from datetime import datetime
from app.core.models import FaceFeature
import os
import re

logger = get_logger(__name__)

# 权限校验装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user:
            print("未登录或未获取到用户信息")
            return {'success': False, 'message': '未登录'}, 401
        role = user.get('role')
        if role != 'admin':
            print("权限不足，当前角色：", role)
            return {'success': False, 'message': '无权限，管理员专用'}, 403
        return f(*args, **kwargs)
    return decorated_function

# 用户管理API
from flask_restx import Namespace, Resource, fields
user_ns = Namespace('user_admin', description='用户管理（仅管理员）')

user_model = user_ns.model('User', {
    'id': fields.Integer,
    'username': fields.String,
    'email': fields.String,
    'role': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
})

user_list_response = user_ns.model('UserListResponse', {
    'success': fields.Boolean,
    'message': fields.String,
    'data': fields.List(fields.Nested(user_model))
})

@user_ns.route('/')
class UserList(Resource):
    @admin_required
    @user_ns.marshal_with(user_list_response)
    def get(self):
        users = User.query.all()
        return {
            'success': True,
            'message': '获取用户列表成功',
            'data': users
        }

@user_ns.route('/<int:user_id>')
class UserDetail(Resource):
    @user_ns.marshal_with(user_model)
    @admin_required
    def get(self, user_id):
        """根据用户ID获取用户信息（仅限管理员）"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        return user

    @admin_required
    def put(self, user_id):
        data = request.json
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        
        user.username = data.get('name', user.username)
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        db.session.commit()

        # 手动序列化 user 数据
        user_data = marshal(user, user_model)
        return {'success': True, 'data': user_data}, 200

    @admin_required
    def delete(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        db.session.delete(user)
        db.session.commit()
        return {'success': True, 'message': '删除成功'}
    
@user_ns.route('/<int:user_id>/faces')
class UserFaceList(Resource):
    @admin_required
    def get(self, user_id):
        """
        获取指定用户的人脸图片列表（管理员操作）
        """
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404

        face_features = FaceFeature.query.filter_by(user_id=user_id).all()

        images = []
        for face in face_features:
            images.append({
                'id': face.id,
                'name': face.name,
                'image_url': face.image_path
            })

        return {'success': True, 'images': images}, 200
    
@user_ns.route('/<int:user_id>/faces/<int:face_id>')
class UserFaceDelete(Resource):
    @admin_required
    def delete(self, user_id, face_id):
        """
        删除指定用户的人脸图片（管理员操作）
        """
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404

        feature = FaceFeature.query.get(face_id)
        if not feature:
            return {'success': False, 'message': '人脸数据不存在'}, 404
        
        if feature.user_id != user_id:
            return {'success': False, 'message': '用户与人脸数据不匹配'}, 400
        
        # 删除图片文件（如果有存储图片）
        if feature.image_path:
            relative_path = feature.image_path.replace('data/', '', 1)
            image_full_path = os.path.join(current_app.root_path, 'static', relative_path)
            if os.path.exists(image_full_path):
                os.remove(image_full_path)

        db.session.delete(feature)
        db.session.commit()
        return {'success': True, 'message': '人脸数据删除成功'}

# 1. 定义一个命名空间 'ns'
ns = Namespace('auth', description='认证相关操作')

# --- 以下是你的认证 API 接口定义示例 ---

# 认证模型 (例如，用于登录请求体)
login_model = ns.model('Login', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码'),
    'captcha': fields.String(required=True, description='验证码')
})

login_response_model = ns.model('LoginResponse', {
    'success': fields.Boolean(description='请求是否成功'),
    'message': fields.String(description='消息提示'),
    'access_token': fields.String(description='JWT访问令牌', required=False),
    'token_type': fields.String(description='令牌类型', default='bearer', required=False)
})

@ns.route('/login')
class UserLogin(Resource):
    @ns.doc('用户登录')
    @ns.expect(login_model, validate=True)
    @ns.marshal_with(login_response_model)
    def post(self):
        """
        处理用户登录请求，验证凭据并返回JWT令牌。
        """
        data = ns.payload
        username = data.get('username')
        password = data.get('password')
        captcha = data.get('captcha')

        # 校验验证码
        code = session.get('captcha_code')

        if not code:
            return {'success': False, 'message': '验证码已过期，请刷新验证码'}, 400
        if not captcha or captcha.upper() != code:
            return {'success': False, 'message': '验证码错误'}, 400
        # 验证通过后清除验证码，防止重用
        session.pop('captcha_code', None)

        # 实际的认证逻辑（例如，查询数据库验证用户名和密码）
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            access_token = create_jwt_token(user)
            return {
                'success': True,
                'message': '登录成功',
                'access_token': access_token,
                'token_type': 'bearer'
            }
        else:
            return {
                'success': False,
                'message': '无效的用户名或密码'
            }

# 邮箱验证码发送请求模型
send_email_code_model = ns.model('SendEmailCode', {
    'email': fields.String(description='邮箱地址'),
    'phone': fields.String(description='手机号或邮箱')
})

# 邮箱验证码登录请求模型
email_login_model = ns.model('EmailLogin', {
    'email': fields.String(required=True, description='邮箱地址'),
    'code': fields.String(required=True, description='验证码')
})

@ns.route('/send_email_code')
class SendEmailCode(Resource):
    @ns.doc('发送邮箱验证码')
    @ns.expect(send_email_code_model, validate=True)
    def post(self):
        """发送邮箱验证码"""
        data = ns.payload
        email = data.get('email') or data.get('phone')
        print("收到邮箱：", email)
        if not email:
            return {'success': False, 'message': '邮箱地址不能为空'}, 400
        try:
            send_email_code(email)
            return {'success': True, 'message': '验证码已发送'}
        except Exception as e:
            return {'success': False, 'message': f'发送失败：{str(e)}'}, 500

@ns.route('/login_email')
class LoginWithEmailCode(Resource):
    @ns.doc('邮箱验证码登录')
    @ns.expect(email_login_model, validate=True)
    @ns.marshal_with(login_response_model)
    def post(self):
        """邮箱验证码登录（仅限已注册用户）"""
        data = ns.payload
        email = data.get('email')
        code = data.get('code')

        if not verify_email_code(email, code):
            return {'success': False, 'message': '验证码无效或已过期'}, 401

        user = User.query.filter_by(email=email).first()
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404

        token = create_jwt_token(user)
        return {
            'success': True,
            'message': '登录成功',
            'access_token': token,
            'token_type': 'bearer'
        }
    
# 注册
register_model = ns.model('Register', {
    'username': fields.String(required=True),
    'email': fields.String(required=True),
    'password': fields.String(required=True),
})

# 通用响应模型
base_response_model = ns.model('BaseResponse', {
    'success': fields.Boolean(description='请求是否成功'),
    'message': fields.String(description='返回的消息')
})


@ns.route('/register')
class UserRegister(Resource):
    @ns.doc('用户注册')
    @ns.expect(register_model)
    @ns.marshal_with(base_response_model)
    def post(self):
        data = ns.payload
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        # 密码强度校验
        ok, msg = self.check_password_strength(password)
        if not ok:
            return {'success': False, 'message': msg}, 400
        if find_user_by_username(username):
            return {'success': False, 'message': '用户名已存在'}, 400
        
        if find_user_by_email(email):
            return {'success': False, 'message': '邮箱已被注册'}, 400

        create_user(username,email,password)
        return {'success': True, 'message': '注册成功'}
    @staticmethod
    def check_password_strength(password):
        if len(password) < 8:
            return False, "密码长度不能少于8位"
        has_lower = re.search(r'[a-z]', password)
        has_upper = re.search(r'[A-Z]', password)
        has_digit = re.search(r'\d', password)
        has_special = re.search(r'[^A-Za-z0-9]', password)
        has_letter = has_lower or has_upper
        if has_letter and has_digit and not has_special:
            return True, "中"
        if has_letter and has_digit and has_special:
            return True, "强"
        return False, "密码过于简单，需包含字母、数字和特殊字符"
    

# 显示当前用户信息
from app.core.security import token_required  # ✅ 导入装饰器
@ns.route('/me')
class UserMe(Resource):
    @ns.doc('获取当前用户信息')
    @token_required
    def get(self):
        user = g.user

        if not user:
            return {'success': False, 'message': '用户不存在'}, 404

        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }
# 你可能还会有注册、刷新token等其他接口
# @ns.route('/register')
# class UserRegister(Resource):
#    ...

# 修改密码（邮箱验证码）
@ns.route('/change_password')
class ChangePassword(Resource):
    @token_required
    def post(self):
        user = g.user
        data = request.json
        code = data.get('code')
        new_password = data.get('new_password')
        if not code or not new_password:
            return {'success': False, 'message': '验证码和新密码不能为空'}, 400
        from ..utils.email_service import verify_email_code
        if not verify_email_code(user.email, code):
            return {'success': False, 'message': '验证码无效或已过期'}, 400
        user.set_password(new_password)
        from ..extensions import db
        db.session.commit()
        return {'success': True, 'message': '密码修改成功'}

# 删除自己的人脸信息（放在 face_recognition.py 里更合适，但这里先实现）
@ns.route('/delete_face/<int:face_id>')
class DeleteFace(Resource):
    @token_required
    def delete(self, face_id):
        user = g.user
        from ..core.models import FaceFeature
        from ..extensions import db
        feature = FaceFeature.query.get(face_id)
        if not feature or feature.user_id != user.id:
            return {'success': False, 'message': '无权限或人脸不存在'}, 403
        db.session.delete(feature)
        db.session.commit()
        try:
            current_app.face_recognition_service.reload_face_database()
        except Exception as e:
            logger.error(f"删除人脸后重载数据库失败: {e}")
            return {'success': False, 'message': '人脸信息删除失败'}
        return {'success': True, 'message': '人脸信息已删除'}
# ... existing code ...
# ... 其他认证相关的Resource ...

@ns.route('/captcha')
class Captcha(Resource):
    def get(self):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        session['captcha_code'] = code
        # session.modified = True  # 可选，强制刷新session
        image = ImageCaptcha(width=120, height=40, font_sizes=[28, 32, 36])
        data = image.generate(code)
        buf = io.BytesIO()
        buf.write(data.read())
        buf.seek(0)
        response = make_response(send_file(buf, mimetype='image/png'))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    
# 修改用户名
@ns.route('/change_username')
class ChangeUsername(Resource):
    @token_required
    def post(self):
        user = g.user
        data = request.json
        new_username = data.get('new_username')
        if not new_username:
            return {'success': False, 'message': '新用户名不能为空'}, 400
        if find_user_by_username(new_username):
            return {'success': False, 'message': '用户名已存在'}, 400        
        user.username = new_username
        from ..extensions import db
        db.session.commit()
        return {'success': True, 'message': '用户名修改成功'}