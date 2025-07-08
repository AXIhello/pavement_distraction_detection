from flask import Flask, request
from flask_restx import Api, Resource, fields

app = Flask(__name__)
# 配置 Swagger UI 路径
# 通常建议将 /doc 设置为文档路径，/swagger_ui 或 /swagger 也可以
api = Api(app,
          version='1.0',
          title='用户管理 API',
          description='这是一个示例的用户管理 API 文档',
          doc='/doc') # Swagger UI 的访问路径

# 定义一个命名空间 (Namespace)，可以把相关的 API 组织在一起
ns = api.namespace('users', description='用户操作')

# 模拟数据库
users_db = {
    "1": {"name": "Alice", "email": "alice@example.com"},
    "2": {"name": "Bob", "email": "bob@example.com"}
}

# --- 定义模型 (Model) ---
# 使用 api.model 来定义数据结构，这会在 Swagger UI 中生成清晰的请求/响应模型
user_model = api.model('User', {
    'id': fields.String(readOnly=True, description='用户的唯一标识符'),
    'name': fields.String(required=True, description='用户的姓名'),
    'email': fields.String(required=True, description='用户的邮箱')
})

# 定义一个用于创建/更新用户的请求体模型（如果与 user_model 略有不同）
user_create_update_model = api.model('UserCreateUpdate', {
    'name': fields.String(required=True, description='用户的姓名'),
    'email': fields.String(required=True, description='用户的邮箱')
})


# --- 定义 API 资源 (Resource) ---
# 每个 Resource 对应一个 API 接口路径
@ns.route('/') # 对应 /users/ 路径
class UserList(Resource):
    @ns.doc('获取所有用户') # 装饰器用于生成该方法的文档
    @ns.marshal_list_with(user_model) # 自动将返回的数据序列化为 user_model 结构
    def get(self):
        """
        返回所有注册用户的信息列表
        """
        return list(users_db.values())

    @ns.doc('创建新用户')
    @ns.expect(user_create_update_model, validate=True) # 期望的请求体模型和开启校验
    @ns.marshal_with(user_model, code=201) # 成功创建返回 201 状态码，并按 user_model 序列化
    def post(self):
        """
        创建一个新用户
        """
        data = api.payload # Flask-RESTx 会自动解析请求体
        new_id = str(len(users_db) + 1)
        users_db[new_id] = {'id': new_id, 'name': data['name'], 'email': data['email']}
        return users_db[new_id], 201

@ns.route('/<string:user_id>') # 对应 /users/<user_id> 路径
@ns.param('user_id', '用户的唯一标识符') # 路径参数的文档
class User(Resource):
    @ns.doc('获取单个用户')
    @ns.marshal_with(user_model)
    @ns.response(404, '用户未找到') # 定义可能的响应状态码及其描述
    def get(self, user_id):
        """
        根据用户ID获取单个用户的信息
        """
        if user_id not in users_db:
            api.abort(404, message=f"用户 {user_id} 未找到") # 使用 api.abort 统一处理错误
        return users_db[user_id]

    @ns.doc('更新用户信息')
    @ns.expect(user_create_update_model, validate=True)
    @ns.marshal_with(user_model)
    @ns.response(404, '用户未找到')
    def put(self, user_id):
        """
        更新现有用户的信息
        """
        if user_id not in users_db:
            api.abort(404, message=f"用户 {user_id} 未找到")
        data = api.payload
        users_db[user_id].update(data)
        return users_db[user_id]

    @ns.doc('删除用户')
    @ns.response(204, '用户删除成功')
    @ns.response(404, '用户未找到')
    def delete(self, user_id):
        """
        删除一个用户
        """
        if user_id not in users_db:
            api.abort(404, message=f"用户 {user_id} 未找到")
        del users_db[user_id]
        return '', 204 # 删除成功通常返回 204 No Content


if __name__ == '__main__':
    app.run(debug=True)