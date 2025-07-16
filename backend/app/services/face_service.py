# 人脸识别的核心业务逻辑

import dlib
import numpy as np
import cv2
import os
import pandas as pd
import base64
import json  # 用于处理 base64 解码和编码
import logging
import tensorflow as tf
from .face_db_service import FaceDatabaseService
# 获取日志器
logger = logging.getLogger(__name__)
# 告警
from .alert_service import save_alert_frame
from datetime import datetime
from pathlib import Path

class FaceRecognitionService:
    def __init__(self, app_config_data):
        self.app_config = app_config_data
        self.detector = None
        self.predictor = None
        self.face_reco_model = None
        self.deepfake_model = None
        self.features_known_list = []
        self.face_name_known_list = []


    def initialize_models(self):
        logger.info("正在加载 Dlib 人脸识别模型...")
        try:
            dlib_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'data_dlib')
            features_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data',
                                             'features_all.csv')

            # 检查 Dlib 模型文件是否存在
            predictor_path = os.path.join(dlib_data_path, 'shape_predictor_68_face_landmarks.dat')
            reco_model_path = os.path.join(dlib_data_path, 'dlib_face_recognition_resnet_model_v1.dat')
            deepfake_model_path = os.path.join(dlib_data_path, 'xception_deepfake_image_5o.h5')
            if not os.path.exists(predictor_path):
                logger.error(f"Dlib 模型文件未找到: {predictor_path}")
                raise FileNotFoundError(f"Missing Dlib predictor: {predictor_path}")
            if not os.path.exists(reco_model_path):
                logger.error(f"Dlib 模型文件未找到: {reco_model_path}")
                raise FileNotFoundError(f"Missing Dlib recognition model: {reco_model_path}")

            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor(predictor_path)
            self.face_reco_model = dlib.face_recognition_model_v1(reco_model_path)
            logger.info("Dlib 模型加载完成。")

            self._load_face_database(features_csv_path)
        except (FileNotFoundError, Exception) as e:
            if isinstance(e, FileNotFoundError):
                logger.error(f"Dlib 或人脸数据库文件缺失: {e}")
            else:
                logger.error(f"初始化 FaceRecognitionService 失败: {e}", exc_info=True)

            self.detector = None
            self.predictor = None
            self.face_reco_model = None
            self.features_known_list = []
            self.face_name_known_list = []
        try:
            self.deepfake_model = tf.keras.models.load_model(deepfake_model_path)
        except Exception as e:
            logger.error(f"加载deepfake检测模型失败: {e}")
            self.deepfake_model = None

    def register_face(self, name, base64_image_data, user_id=None):
        """
        注册新的人脸到数据库
        Args:
            name: 人名
            base64_image_data: Base64编码的图像数据
            user_id: 用户ID
        Returns:
            注册结果字典
        """

        if not self.detector or not self.predictor or not self.face_reco_model:
            logger.error("Dlib 模型未加载。无法执行注册。")
            return {'success': False, 'message': 'Dlib models not loaded.'}

        try:
            # 解析Base64图像
            header, encoded_image = base64_image_data.split(',')
            nparr = np.frombuffer(base64.b64decode(encoded_image), np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_np is None:
                return {'success': False, 'message': '无法解码图像数据'}

            # 转换为RGB
            img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)

            # 检测人脸
            faces = self.detector(img_rgb, 0)

            if len(faces) == 0:
                return {'success': False, 'message': '未检测到人脸，请确保图像中包含清晰的人脸'}

            if len(faces) > 1:
                return {'success': False, 'message': '检测到多个人脸，请只包含一个人脸'}

            # 提取人脸特征
            face = faces[0]
            shape = self.predictor(img_rgb, face)
            face_descriptor = self.face_reco_model.compute_face_descriptor(img_rgb, shape)
            face_descriptor_np = np.array(face_descriptor)
            #查重，是否已经存在同样的人脸
            from .face_db_service import FaceDatabaseService
            all_features = FaceDatabaseService.get_all_features()
            duplicate_name = None
            for exist_name, exist_feature in all_features:
                dist = np.linalg.norm(face_descriptor_np - exist_feature)
                if dist < 0.5:  # 阈值可调整
                    duplicate_name = exist_name
                    break
            if duplicate_name:
                if duplicate_name == name:
                    # 允许注册，后续会走平均特征逻辑
                    pass
                else:
                    return {
                        'success': False,
                        'message': f'该人脸已被注册为 {duplicate_name}，请勿用其他名字重复录入'
                    }
            #保存图片
            save_dir = f"data/data_faces_from_camera/person_{name}"
            os.makedirs(save_dir, exist_ok=True)
            from .face_db_service import FaceDatabaseService
            feature_count = FaceDatabaseService.get_feature_count(name)
            img_path = os.path.join(save_dir, f"img_face_{feature_count + 1}.jpg")
            cv2.imwrite(img_path, img_np)

            # 保存到数据库，传递 image_path
            success = FaceDatabaseService.save_feature(name, face_descriptor_np, user_id, image_path=img_path)
            #success = FaceDatabaseService.save_feature(name, face_descriptor_np, user_id)

            if success:
                # 重新加载人脸数据库
                self.reload_face_database()
                logger.info(f"成功注册人脸: {name}")
                return {
                    'success': True,
                    'message': f'成功注册 {name} 的人脸特征',
                    'name': name
                }
            else:
                return {'success': False, 'message': '保存到数据库失败'}

        except Exception as e:
            logger.error(f"人脸注册失败: {e}", exc_info=True)
            return {'success': False, 'message': f'注册失败: {str(e)}'}

    def _load_face_database(self, path_features_known_csv=None):

        self.features_known_list = []
        self.face_name_known_list = []
        
        try:
            # 从数据库服务获取所有特征
            from .face_db_service import FaceDatabaseService
            features_data = FaceDatabaseService.get_all_features()
            
            for name, feature_vector in features_data:
                self.face_name_known_list.append(name)
                self.features_known_list.append(feature_vector.astype(np.float64))
            
            logger.info(f"从数据库加载人脸特征完成，已包含 {len(self.features_known_list)} 张已知人脸。")
            
        except Exception as e:
            logger.error(f"从数据库加载人脸特征失败: {e}", exc_info=True)
            self.features_known_list = []
            self.face_name_known_list = []
    
    def reload_face_database(self):
        """
        重新加载人脸数据库（无参数版本）
        """
        self._load_face_database()

    def _return_euclidean_distance(self, feature_1, feature_2):
        """
        计算两个 128D 人脸特征之间的欧式距离。
        """
        return np.linalg.norm(feature_1 - feature_2)

    def recognize_face(self, base64_image_data):
        """
        对 Base64 编码的图像数据进行人脸识别。
        Args:
            base64_image_data: 前端发送的 Base64 图像字符串 (包含 'data:image/jpeg;base64,' 前缀)。
        Returns:
            一个包含识别结果的列表。
        """
        if not self.detector or not self.predictor or not self.face_reco_model:
            logger.error("Dlib 模型未加载。无法执行识别。")
            return [{"status": "error", "message": "Dlib models not loaded."}]

        try:
            header, encoded_image = base64_image_data.split(',')

            # 解码 Base64 图像
            nparr = np.frombuffer(base64.b64decode(encoded_image), np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_np is None:
                logger.warning("无法解码图像数据。")
                return [{"status": "error", "message": "Invalid image data."}]

            # 将 BGR 转换为 RGB
            img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)

            faces = self.detector(img_rgb, 0)  # 0 代表不向上采样

            recognition_results = []
            if len(faces) > 0:
                for i, d in enumerate(faces):
                    #裁剪人脸区域
                    face_img = img_rgb[d.top():d.bottom(), d.left():d.right()]
                    if face_img.size == 0:
                        continue
                    face_img_resized = cv2.resize(face_img, (224, 224))
                    #送入deepfake监测模型
                    face_img_processed =  tf.keras.applications.xception.preprocess_input(face_img_resized)
                    pred = self.deepfake_model.predict(np.expand_dims(face_img_processed, axis=0))
                    # 提取人脸特征点
                    shape = self.predictor(img_rgb, d)
                    # 提取 128D 人脸特征
                    face_descriptor = self.face_reco_model.compute_face_descriptor(img_rgb, shape)
                    face_descriptor_np = np.array(face_descriptor)  # 转换为 numpy 数组以便计算

                    min_dist = float('inf')
                    recognized_name = "未知人员"

                    # 先进行DeepFake检测
                    fake_prob = float(pred[0][0]) if pred is not None else None
                    is_deepfake = fake_prob is not None and fake_prob > 0.6
                    
                    if is_deepfake:
                        # 如果是DeepFake，直接返回deepfake身份
                        recognized_name = "deepfake"
                        logger.warning(f"!!! DeepFake警告: 概率: {fake_prob:.4f}，位置: {d.left()},{d.top()},{d.right()},{d.bottom()}")
                        # 写入告警模块
                        # 自动生成保存路径
                        now = datetime.now()
                        timestamp = now.strftime('%Y%m%d_%H%M%S')
                        save_dir = Path(f'data/alert_videos/face')

                        face_img_bgr = cv2.cvtColor(face_img_resized, cv2.COLOR_RGB2BGR)
                        _, buffer = cv2.imencode('.jpg', face_img_bgr)
                        image_bytes = base64.b64encode(buffer).decode('utf-8')
                        # 人脸告警帧
                        save_alert_frame('face', f'data:image/jpeg;base64,{image_bytes}', confidence=fake_prob,disease_type="deepfake",save_dir0=str(save_dir))

                    else:
                        # 如果不是DeepFake，进行正常的人脸识别
                        # 遍历已知人脸库进行比对
                        if self.features_known_list:
                            for j, known_feature in enumerate(self.features_known_list):
                                dist = self._return_euclidean_distance(face_descriptor_np, known_feature)
                                if dist < min_dist:
                                    min_dist = dist
                                    if min_dist < 0.5:  # 设置一个阈值，小于这个距离认为是同一个人
                                        recognized_name = self.face_name_known_list[j]
                                    else:
                                        recognized_name = "陌生人"
                                        # 写入告警模块
                                        # 自动生成保存路径
                                        save_dir = Path(f'data/alert_videos/face')
                                        save_dir.mkdir(parents=True, exist_ok=True)  # 确保目录存在
                                        face_img_bgr = cv2.cvtColor(face_img_resized, cv2.COLOR_RGB2BGR)
                                        _, buffer = cv2.imencode('.jpg', face_img_resized)
                                        image_bytes = base64.b64encode(buffer).decode('utf-8')
                                        # 人脸告警帧
                                        distance = round(min_dist, 3) if min_dist != float('inf') else None
                                        save_alert_frame('face', f'data:image/jpeg;base64,{image_bytes}', confidence=distance,disease_type="陌生人",save_dir0=str(save_dir))


                    recognition_results.append({
                        "face_id": i,
                        "name": recognized_name,
                        "distance": round(min_dist, 3) if min_dist != float('inf') else None,  
                        "bbox": {"left": d.left(), "top": d.top(), "right": d.right(), "bottom": d.bottom()}
                    })
                    logger.info(
                        f"检测到人脸: {recognized_name} (距离: {min_dist:.3f})"
                    )

            else:
                logger.info("未检测到人脸。")
                recognition_results.append({"name": "未检测到人脸", "status": "no_face"})

            return recognition_results

        except Exception as e:
            logger.error(f"人脸识别服务处理图像失败: {e}", exc_info=True)
            return [{"status": "error", "message": f"Processing error: {e}"}]

    def extract_all_features_to_csv(self):
        """
        提取所有已录入人脸的128D特征，生成 features_all.csv（兼容性方法，现在没有使用）
        """
        try:
            from .face_db_service import FaceDatabaseService
            features_data = FaceDatabaseService.get_all_features()
            
            if not features_data:
                return {'success': False, 'message': '数据库中没有特征数据'}
            
            # 创建CSV文件
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'features_all.csv')
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # 写入CSV
            with open(csv_path, 'w', newline='') as csvfile:
                csvfile.write('name,feature\n')
                for name, feature_vector in features_data:
                    feature_str = ','.join(map(str, feature_vector))
                    csvfile.write(f'{name},{feature_str}\n')
            
            logger.info(f"成功导出 {len(features_data)} 个特征到 {csv_path}")
            return {
                'success': True, 
                'message': f'成功导出 {len(features_data)} 个特征到CSV文件',
                'file_path': csv_path
            }
        except Exception as e:
            logger.error(f"特征导出失败: {e}", exc_info=True)
            return {'success': False, 'message': f'特征导出失败: {str(e)}'}