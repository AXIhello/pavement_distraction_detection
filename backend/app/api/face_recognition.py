from flask_restx import Namespace, Resource

ns = Namespace('face', description='人脸识别相关接口')

@ns.route('/ping')
class FacePing(Resource):
    def get(self):
        """健康检查接口"""
        return {'message': 'face api ok'}