from turtle import distance
from flask_restx import Namespace, Resource, fields
from flask import request, current_app, g
import logging
from ..core.models import FaceFeature, db
from functools import wraps
from ..services.alert_service import save_alert_frame
from datetime import datetime
from pathlib import Path
import hashlib
from flask import jsonify


# 获取日志器
logger = logging.getLogger(__name__)
ns = Namespace('face', description='人脸识别相关接口')

# 请求体模型
face_register_model = ns.model('FaceRegister', {
    'name': fields.String(required=True, description='姓名', example='张三'),
    'image': fields.String(required=True, description='Base64图片', example='data:image/jpeg;base64,...')
})

face_recognition_model = ns.model('FaceRecognition', {
    'image': fields.String(required=True, description='Base64图片', example='data:image/jpeg;base64,...')
})

face_register_response_model = ns.model('FaceRegisterResponse', {
    'success': fields.Boolean(description='是否成功', example=True),
    'message': fields.String(description='提示信息', example='成功注册 张三 的人脸特征'),
    'face_id': fields.Integer(description='人脸特征ID', example=1)
})

face_recognition_result_model = ns.model('FaceRecognitionResult', {
    'face_id': fields.Integer(description='人脸编号', example=0),
    'name': fields.String(description='识别到的姓名', example='张三'),
    'distance': fields.Float(description='欧氏距离', example=0.32),
    'bbox': fields.Raw(description='人脸框坐标', example={'left': 10, 'top': 20, 'right': 100, 'bottom': 120})
})

face_recognition_response_model = ns.model('FaceRecognitionResponse', {
    'success': fields.Boolean(description='是否成功', example=True),
    'faces': fields.List(fields.Nested(face_recognition_result_model), description='识别结果列表')
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

# 新增：保存人脸告警帧接口
face_alert_frame_model = ns.model('FaceAlertFrame', {
    'image': fields.String(required=True, description='Base64图片'),
    'type': fields.String(required=True, description='告警类型'),
    'confidence': fields.Float(required=True, description='置信度')
})


@ns.route('/register')
class FaceRegister(Resource):
    @ns.doc('人脸注册', description='注册新的人脸特征，需登录', security='jwt')
    @ns.expect(face_register_model, validate=True)
    @ns.marshal_with(face_register_response_model)
    @ns.response(200, '注册成功')
    @ns.response(400, '参数错误或未检测到人脸')
    @ns.response(401, '未登录')
    @ns.response(500, '服务器内部错误')
    def post(self):
        """
        人脸图片录入接口。
        参数：姓名、Base64图片。
        返回：注册结果。
        """
        try:
            data = ns.payload
            name = data.get('name')
            image_base64 = data.get('image')
            user = getattr(g, 'user', None)
            user_id = user['id'] if user else None

            logger.info(
                f"收到人脸注册请求: name={name}, user_id={user_id}, image_length={len(image_base64) if image_base64 else 0}")

            if not user_id:
                return {'success': False, 'message': '未获取到用户ID，请登录后操作'}, 401

            # 直接调用业务逻辑服务进行人脸注册
            service = current_app.face_recognition_service
            result = service.register_face(name, image_base64, user_id)

            if result.get('success'):
                # 注册成功后，获取数据库中的记录ID
                try:
                    feature_record = FaceFeature.get_by_name(name)
                    if feature_record:
                        # 更新user_id字段
                        feature_record.user_id = user_id
                        db.session.commit()

                        return {
                            'success': True,
                            'message': result.get('message', '注册成功'),
                            'face_id': feature_record.id
                        }
                    else:
                        logger.warning(f"注册成功但未找到 {name} 的记录")
                        return {
                            'success': True,
                            'message': result.get('message', '注册成功'),
                            'face_id': None
                        }
                except Exception as e:
                    logger.error(f"更新user_id失败: {e}")
                    # 即使更新user_id失败，人脸注册本身是成功的
                    return {
                        'success': True,
                        'message': result.get('message', '注册成功'),
                        'face_id': None
                    }
            else:
                return {
                    'success': False,
                    'message': result.get('message', '注册失败')
                }

        except Exception as e:
            logger.error(f"人脸注册接口处理失败: {e}", exc_info=True)
            return {'success': False, 'message': f'注册失败: {str(e)}'}

@ns.route('/recognize')
class FaceRecognition(Resource):
    @ns.doc('人脸识别', description='对单张图片进行人脸识别', security='jwt')
    @ns.expect(face_recognition_model, validate=True)
    @ns.marshal_with(face_recognition_response_model)
    @ns.response(200, '识别成功')
    @ns.response(400, '缺少图片数据')
    @ns.response(401, '未登录')
    @ns.response(500, '服务器内部错误')
    def post(self):
        """
        人脸识别接口（用于单张图片识别）。
        参数：Base64图片。
        返回：识别结果。
        """
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

            # 告警模块
            if recognition_results[0].get("name") == "陌生人" or recognition_results[0].get("name") == "deepfake":                # 1️. 自动生成保存路径
                now = datetime.now()
                timestamp = now.strftime('%Y%m%d_%H%M%S')
                save_dir = Path(f'data/alert_videos/face/video_{timestamp}')
                save_dir.mkdir(parents=True, exist_ok=True)
                if(recognition_results[0].get("distance") != None):
                    confidence = 1 - recognition_results[0].get("distance")
                else: confidence = 0.1
                save_alert_frame(
                    "face",
                    image_base64,
                    confidence,
                    disease_type=recognition_results[0].get("name"),
                    save_dir0=str(save_dir)
                )

            return {
                'success': True,
                'faces': recognition_results
            }
            
        except Exception as e:
            logger.error(f"人脸识别接口处理失败: {e}", exc_info=True)
            return {'success': False, 'message': f'识别失败: {str(e)}'}


@ns.route('/save_frame')
class SaveFaceFrame(Resource):
    def post(self):
        data = request.json
        session_id = data.get('session_id')
        image = data.get('image')
        frame_index = data.get('frame_index', 0)
        if not session_id or not image:
            return {'success': False, 'message': '缺少参数'}, 400
        from pathlib import Path
        import base64, io
        from PIL import Image
        save_dir = Path(f'data/alert_videos/face/{session_id}')
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f'frame_{frame_index:05d}.jpg'
        # 保存图片
        if image and ',' in image:
            image_base64 = image.split(',')[1]
        else:
            image_base64 = image
        image_data = base64.b64decode(image_base64)
        image_pil = Image.open(io.BytesIO(image_data))
        if image_pil.mode == 'RGBA':
            image_pil = image_pil.convert('RGB')
        image_pil.save(save_path)
        return {'success': True, 'path': str(save_path)}

@ns.route('/alert_judgement')
class FaceAlertJudgement(Resource):
    def post(self):
        """
        视频/摄像头流式识别的最终判定接口。
        只处理视频和摄像头模式的告警写入，单张图片识别不调用此接口。
        """
        try:
            data = request.json
            session_id = data.get('session_id')
            result = data.get('result')  # 'normal', 'deepfake', 'stranger'
            confidence = data.get('confidence', 1)
            logger.info(f"[DEBUG] 收到告警判定请求: session_id={session_id}, result={result}, confidence={confidence}")
            if not session_id or not result:
                logger.error(f"[ERROR] 缺少参数: session_id={session_id}, result={result}")
                return {'success': False, 'message': '缺少参数'}, 400
            folder_path = f'data/alert_videos/face/{session_id}'
            logger.info(f"[DEBUG] 检查文件夹路径: {folder_path}")
            import shutil, os
            from app.extensions import db
            from app.core.models import FaceAlertFrame
            if result == 'normal':
                # 正常情况，删除临时文件夹
                logger.info(f"[DEBUG] 正常情况，删除文件夹: {folder_path}")
                shutil.rmtree(folder_path, ignore_errors=True)
                logger.info(f"视频/摄像头识别正常，已删除临时文件夹: {folder_path}")
                return {'success': True, 'message': '正常，已删除文件夹', 'result': 'normal'}
            else:
                # 告警情况，写入数据库
                logger.info(f"[DEBUG] 告警情况，检查文件夹是否存在: {folder_path}")
                if not os.path.exists(folder_path):
                    logger.error(f"[ERROR] 文件夹不存在: {folder_path}")
                    return {'success': False, 'message': f'文件夹不存在: {folder_path}', 'result': result}, 44
                # 写入前查重，确保每个 session_id 只写一条
                exist = FaceAlertFrame.query.filter_by(image_path=folder_path).first()
                if exist:
                    logger.info(f"视频/摄像头告警已存在，不重复写入: session_id={session_id}")
                    return {'success': True, 'message': '该告警已存在，不重复写入', 'result': result}
                logger.info(f"[DEBUG] 创建告警记录: image_path={folder_path}, alert_type={result}, confidence={confidence}")
                alert_frame = FaceAlertFrame(
                    image_path=folder_path,
                    alert_type=result,
                    confidence=confidence
                )
                db.session.add(alert_frame)
                db.session.commit()
                logger.info(f"视频/摄像头告警已记录: session_id={session_id}, type={result}, confidence={confidence}")
                return {'success': True, 'message': '告警已记录', 'result': result}
        except Exception as e:
            logger.error(f"视频/摄像头告警判定失败: {e}", exc_info=True)
            return {'success': False, 'message': f'告警判定失败: {str(e)}', 'result': 'error'}, 500

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

# 特征提取接口
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

@ns.route('/my_faces')
class MyFaces(Resource):
    def get(self):
        user = getattr(g, 'user', None)
        if not user:
            return {'success': False, 'message': '未登录'}, 401
        # 查询该用户所有人脸图片
        features = FaceFeature.query.filter_by(user_id=user['id']).all()
        # 返回图片对象列表（包含id和url）
        image_objs = []
        for f in features:
            if f.image_path:
                rel_path = f.image_path.replace("\\", "/")
                if rel_path.startswith("data/"):
                    rel_path = rel_path[5:]
                image_objs.append({
                    'id': f.id,
                    'url': f"/static/{rel_path}",
                    'name': f.name
                })
        return {
            'success': True,
            'images': image_objs
        }

@ns.route('/user_faces/<int:user_id>')
class UserFaces(Resource):
    def get(self, user_id):
        """根据user_id查询该用户所有人脸信息（face_id和name）"""
        from ..core.models import FaceFeature
        features = FaceFeature.query.filter_by(user_id=user_id).all()
        result = [
            {'face_id': f.id, 'name': f.name}
            for f in features
        ]
        return {'success': True, 'faces': result}
