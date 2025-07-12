from flask_restx import Namespace, Resource, fields
from flask import request
import os
import base64
import re
import dlib
import numpy as np
import cv2
import csv
import logging
from ..services.face_db_service import FaceDatabaseService

# 获取日志器
logger = logging.getLogger(__name__)
ns = Namespace('face', description='人脸识别相关接口')

# 人脸录入请求体模型
face_register_model = ns.model('FaceRegister', {
    'name': fields.String(required=True, description='姓名'),
    'image': fields.String(required=True, description='Base64图片')
})

@ns.route('/register')
class FaceRegister(Resource):
    @ns.expect(face_register_model)
    def post(self):
        """人脸图片录入（保存到本地，并立即提取特征追加到 features_all.csv）"""
        data = ns.payload
        name = data.get('name')
        image_base64 = data.get('image')
        logger.info(f"收到请求: name={name}, image_length={len(image_base64)}")
        if not name or not image_base64:
            return {'success': False, 'message': '缺少姓名或图片'}
        # 只保留中文、英文、数字
        name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', name)
        # 使用绝对路径，基于当前文件位置计算项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        save_dir = os.path.join(project_root, 'backend', 'data', 'data_faces_from_camera', f'person_{name}')
        os.makedirs(save_dir, exist_ok=True)
        # 自动编号
        existing = [f for f in os.listdir(save_dir) if f.endswith('.jpg')]
        idx = len(existing) + 1
        img_path = os.path.join(save_dir, f'img_face_{idx}.jpg')
        # 去掉base64头
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        with open(img_path, 'wb') as f:
            f.write(base64.b64decode(image_base64))
        # --- 新增：保存后立即提取特征并加密存储到数据库 ---
        dlib_data_path = os.path.join(project_root, 'backend', 'data', 'data_dlib')
        predictor_path = os.path.join(dlib_data_path, 'shape_predictor_68_face_landmarks.dat')
        reco_model_path = os.path.join(dlib_data_path, 'dlib_face_recognition_resnet_model_v1.dat')
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(predictor_path)
        face_reco_model = dlib.face_recognition_model_v1(reco_model_path)
        img = cv2.imread(img_path)
        if img is not None:
            faces = detector(img, 1)
            if len(faces) > 0:
                shape = predictor(img, faces[0])
                feat = np.array(face_reco_model.compute_face_descriptor(img, shape))
                
                # 使用数据库服务保存加密特征
                success = FaceDatabaseService.save_feature(name, feat)
                if success:
                    feature_count = FaceDatabaseService.get_feature_count(name)
                    
                    # 重新加载人脸识别服务的数据库
                    try:
                        from ..main import face_recognition_service
                        face_recognition_service.reload_face_database()
                        logger.info(f"人脸录入成功后重新加载数据库，当前数据库包含 {len(face_recognition_service.features_known_list)} 个特征")
                    except Exception as e:
                        logger.error(f"重新加载人脸数据库失败: {e}")
                    
                    return {'success': True, 'message': f'保存成功: {img_path}，已录入 {feature_count} 张照片，特征已更新'}
                else:
                    return {'success': False, 'message': '特征保存到数据库失败'}
            else:
                return {'success': False, 'message': '图片中未检测到人脸，未写入特征'}
        else:
            return {'success': False, 'message': '图片保存失败，无法读取'}

# 人脸特征管理接口
@ns.route('/features')
class FaceFeaturesManagement(Resource):
    def get(self):
        """获取所有已注册的人脸特征信息"""
        try:
            names = FaceDatabaseService.get_all_names()
            features_info = []
            for name in names:
                count = FaceDatabaseService.get_feature_count(name)
                features_info.append({
                    'name': name,
                    'photo_count': count  # 改为photo_count更准确
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
            feature_vector = FaceDatabaseService.get_feature(name)
            if feature_vector is not None:
                count = FaceDatabaseService.get_feature_count(name)
                return {
                    'success': True,
                    'data': {
                        'name': name,
                        'photo_count': count,  # 改为photo_count
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
            success = FaceDatabaseService.delete_feature(name)
            if success:
                # 重新加载人脸识别服务的数据库
                try:
                    from ..main import face_recognition_service
                    face_recognition_service.reload_face_database()
                    logger.info(f"删除人脸特征后重新加载数据库，当前数据库包含 {len(face_recognition_service.features_known_list)} 个特征")
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
            # 使用绝对路径，基于当前文件位置计算项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            faces_dir = os.path.join(project_root, 'backend', 'data', 'data_faces_from_camera')
            features_csv = os.path.join(project_root, 'backend', 'data', 'features_all.csv')
            dlib_data_path = os.path.join(project_root, 'backend', 'data', 'data_dlib')
            predictor_path = os.path.join(dlib_data_path, 'shape_predictor_68_face_landmarks.dat')
            reco_model_path = os.path.join(dlib_data_path, 'dlib_face_recognition_resnet_model_v1.dat')
            detector = dlib.get_frontal_face_detector()
            predictor = dlib.shape_predictor(predictor_path)
            face_reco_model = dlib.face_recognition_model_v1(reco_model_path)

            def return_128d_features(img_path):
                img = cv2.imread(img_path)
                if img is None:
                    return None
                faces = detector(img, 1)
                if len(faces) == 0:
                    return None
                shape = predictor(img, faces[0])
                return np.array(face_reco_model.compute_face_descriptor(img, shape))

            person_list = [p for p in os.listdir(faces_dir) if os.path.isdir(os.path.join(faces_dir, p))]
            with open(features_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # 写入注释行
                writer.writerow(['# 人脸特征数据库 - 姓名,特征1,特征2,...,特征128'])
                for person in person_list:
                    person_name = person.split('_', 1)[-1]
                    img_dir = os.path.join(faces_dir, person)
                    features = []
                    for img_file in os.listdir(img_dir):
                        if img_file.endswith('.jpg'):
                            feat = return_128d_features(os.path.join(img_dir, img_file))
                            if feat is not None:
                                features.append(feat)
                    if features:
                        mean_feat = np.mean(features, axis=0)
                    else:
                        mean_feat = np.zeros(128)
                    row = [person_name] + mean_feat.tolist()
                    writer.writerow(row)
            return {'success': True, 'message': '特征提取完成'}
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return {'success': False, 'message': f'特征提取失败: {str(e)}'}