# 认证相关接口
# backend/app/api/auth.py
from flask_restx import Namespace, Resource, fields
from ..core.models import User, find_user_by_username, find_user_by_email, create_user
from ..core.security import create_jwt_token
from flask import current_app, Blueprint, request, jsonify, g
from ..utils.email_service import send_email_code, verify_email_code
from functools import wraps
from ..extensions import db

# 权限校验装饰器

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'message': '无权限，管理员专用'}), 403
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

@user_ns.route('/')
class UserList(Resource):
    @user_ns.marshal_list_with(user_model)
    @admin_required
    def get(self):
        users = User.query.all()
        return users

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

    @user_ns.marshal_with(user_model)
    @admin_required
    def put(self, user_id):
        data = request.json
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        db.session.commit()
        return user

    @admin_required
    def delete(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}, 404
        db.session.delete(user)
        db.session.commit()
        return {'success': True, 'message': '删除成功'}

# 1. 定义一个命名空间 'ns'
ns = Namespace('auth', description='认证相关操作')

# --- 以下是你的认证 API 接口定义示例 ---

# 认证模型 (例如，用于登录请求体)
login_model = ns.model('Login', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码')
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

        # 实际的认证逻辑（例如，查询数据库验证用户名和密码）
        # 已更换为数据库查询
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):  # 这里建议改成密码哈希校验
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
            }, 401

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

        if find_user_by_username(username):
            return {'success': False, 'message': '用户名已存在'}, 400
        
        if find_user_by_email(email):
            return {'success': False, 'message': '邮箱已被注册'}, 400

        create_user(username,email,password)
        return {'success': True, 'message': '注册成功'}
        
# 你可能还会有注册、刷新token等其他接口
# @ns.route('/register')
# class UserRegister(Resource):
#    ...

# ... 其他认证相关的Resource ...