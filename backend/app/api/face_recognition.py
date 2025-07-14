from flask_restx import Namespace, Resource, fields
from flask import request, current_app, g
import logging
from ..core.models import FaceFeature, db
from functools import wraps

# 获取日志器
logger = logging.getLogger(__name__)
ns = Namespace('face', description='人脸识别相关接口')

# 请求体模型
face_register_model = ns.model('FaceRegister', {
    'name': fields.String(required=True, description='姓名'),
    'image': fields.String(required=True, description='Base64图片')
})

face_recognition_model = ns.model('FaceRecognition', {
    'image': fields.String(required=True, description='Base64图片')
})

# 权限校验装饰器

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user or user.get('role') != 'admin':
            return {'success': False, 'message': '无权限，管理员专用'}, 403
        return f(*args, **kwargs)
    return decorated_function

face_feature_ns = Namespace('face_features', description='人脸特征管理')

face_feature_model = face_feature_ns.model('FaceFeature', {
    'id': fields.Integer,
    'name': fields.String,
    'user_id': fields.Integer,
    'feature_count': fields.Integer,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
})

@ns.route('/register')
class FaceRegister(Resource):
    @ns.expect(face_register_model)
    def post(self):
        """人脸图片录入接口"""
        try:
            data = ns.payload
            name = data.get('name')
            image_base64 = data.get('image')
            #user = getattr(g, 'user', None)
            #user_id = user['id'] if user else None
            #logger.info(f"收到人脸注册请求: name={name}, user_id={user_id}, image_length={len(image_base64) if image_base64 else 0}")
            #if not user_id:
            #    return {'success': False, 'message': '未获取到用户ID，请登录后操作'}, 401
            # 业务逻辑：写入FaceFeature表
                # 调用业务逻辑服务
            service = current_app.face_recognition_service
            result = service.register_face(name, image_base64)
            # 实际业务应在此处提取特征并更新feature_encrypted字段
            return {'success': True, 'message': '人脸录入成功', 'face_id': 0}#feature.id
        except Exception as e:
            logger.error(f"人脸注册接口处理失败: {e}", exc_info=True)
            return {'success': False, 'message': f'注册失败: {str(e)}'}

@ns.route('/recognize')
class FaceRecognition(Resource):
    @ns.expect(face_recognition_model)
    def post(self):
        """人脸识别接口（用于单张图片识别）"""
        try:
            data = ns.payload
            image_base64 = data.get('image')
            
            logger.info(f"收到人脸识别请求: image_length={len(image_base64) if image_base64 else 0}")
            
            if not image_base64:
                return {'success': False, 'message': '缺少图片数据'}
            
            # 调用业务逻辑服务
            service = current_app.face_recognition_service
            recognition_results = service.recognize_face(image_base64)
            
            if not recognition_results:
                return {'success': False, 'message': '识别失败，未返回结果'}
            
            # 检查是否有错误
            if recognition_results[0].get("status") == "error":
                return {
                    'success': False, 
                    'message': recognition_results[0].get("message", "识别出错")
                }
            
            # 检查是否检测到人脸
            if recognition_results[0].get("name") == "未检测到人脸":
                return {
                    'success': False, 
                    'message': '未检测到人脸'
                }
            
            return {
                'success': True,
                'faces': recognition_results
            }
            
        except Exception as e:
            logger.error(f"人脸识别接口处理失败: {e}", exc_info=True)
            return {'success': False, 'message': f'识别失败: {str(e)}'}

# 人脸特征管理接口
@ns.route('/features')
class FaceFeaturesManagement(Resource):
    def get(self):
        """获取所有已注册的人脸特征信息"""
        try:
            from ..services.face_db_service import FaceDatabaseService
            names = FaceDatabaseService.get_all_names()
            features_info = []
            for name in names:
                count = FaceDatabaseService.get_feature_count(name)
                features_info.append({
                    'name': name,
                    'photo_count': count
                })
            return {
                'success': True, 
                'data': features_info,
                'message': f'共找到 {len(features_info)} 个注册用户'
            }
        except Exception as e:
            logger.error(f"获取人脸特征信息失败: {e}")
            return {'success': False, 'message': f'获取失败: {str(e)}'}

@ns.route('/features/<string:name>')
class FaceFeatureDetail(Resource):
    def get(self, name):
        """获取指定人的特征信息"""
        try:
            from ..services.face_db_service import FaceDatabaseService
            feature_vector = FaceDatabaseService.get_feature(name)
            if feature_vector is not None:
                count = FaceDatabaseService.get_feature_count(name)
                return {
                    'success': True,
                    'data': {
                        'name': name,
                        'photo_count': count,
                        'feature_dimension': len(feature_vector)
                    },
                    'message': '获取成功'
                }
            else:
                return {'success': False, 'message': f'未找到 {name} 的特征记录'}
        except Exception as e:
            logger.error(f"获取 {name} 的特征信息失败: {e}")
            return {'success': False, 'message': f'获取失败: {str(e)}'}
    
    def delete(self, name):
        """删除指定人的人脸特征"""
        try:
            from ..services.face_db_service import FaceDatabaseService
            success = FaceDatabaseService.delete_feature(name)
            if success:
                # 重新加载人脸识别服务的数据库
                try:
                    service = current_app.face_recognition_service
                    service.reload_face_database()
                    logger.info(f"删除人脸特征后重新加载数据库，当前数据库包含 {len(service.features_known_list)} 个特征")
                except Exception as e:
                    logger.error(f"重新加载人脸数据库失败: {e}")
                
                return {'success': True, 'message': f'成功删除 {name} 的人脸特征'}
            else:
                return {'success': False, 'message': f'未找到 {name} 的特征记录'}
        except Exception as e:
            logger.error(f"删除 {name} 的特征失败: {e}")
            return {'success': False, 'message': f'删除失败: {str(e)}'}

# 特征提取接口（保留用于兼容性）
@ns.route('/features_extract')
class FaceFeaturesExtract(Resource):
    def post(self):
        """提取所有已录入人脸的128D特征，生成 features_all.csv（兼容性接口）"""
        try:
            service = current_app.face_recognition_service
            result = service.extract_all_features_to_csv()
            return result
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return {'success': False, 'message': f'特征提取失败: {str(e)}'}

@face_feature_ns.route('/user/<int:user_id>')
class FaceFeatureByUser(Resource):
    @face_feature_ns.marshal_list_with(face_feature_model)
    @admin_required
    def get(self, user_id):
        features = FaceFeature.query.filter_by(user_id=user_id).all()
        return features

@face_feature_ns.route('/<int:face_id>')
class FaceFeatureDelete(Resource):
    @admin_required
    def delete(self, face_id):
        feature = FaceFeature.query.get(face_id)
        if not feature:
            return {'success': False, 'message': '人脸信息不存在'}, 404
        db.session.delete(feature)
        db.session.commit()
        return {'success': True, 'message': '人脸信息已删除'}