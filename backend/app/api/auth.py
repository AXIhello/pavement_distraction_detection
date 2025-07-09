# 认证相关接口
# backend/app/api/auth.py
from flask_restx import Namespace, Resource, fields
from app.core.models import User
from app.core.security import create_jwt_token

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
        
        
# 你可能还会有注册、刷新token等其他接口
# @ns.route('/register')
# class UserRegister(Resource):
#    ...

# ... 其他认证相关的Resource ...