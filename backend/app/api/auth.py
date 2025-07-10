# 认证相关接口
# backend/app/api/auth.py
from flask_restx import Namespace, Resource, fields
from app.core.models import User
from app.core.security import create_jwt_token
from flask import current_app
from app.utils.email_service import send_email_code, verify_email_code


# 1. 定义一个命名空间 'ns'
ns = Namespace('auth', description='认证相关操作')

# --- 以下是你的认证 API 接口定义示例 ---

# 认证模型 (例如，用于登录请求体)
login_model = ns.model('Login', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码')
})

# 响应模型 (例如，登录成功后的 token)
# auth_success_model = ns.model('AuthSuccess', {
#     'access_token': fields.String(description='JWT 访问令牌'),
#     'token_type': fields.String(default='bearer')
# })

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
        if user and user.password == password:  # 这里建议改成密码哈希校验
            access_token = create_jwt_token(user.id)
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

        token = create_jwt_token(user.id)
        return {
            'success': True,
            'message': '登录成功',
            'access_token': token,
            'token_type': 'bearer'
        }

        
# 你可能还会有注册、刷新token等其他接口
# @ns.route('/register')
# class UserRegister(Resource):
#    ...

# ... 其他认证相关的Resource ...