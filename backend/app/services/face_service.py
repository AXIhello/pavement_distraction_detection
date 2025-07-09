# 人脸识别的核心业务逻辑

import dlib
import numpy as np
import cv2
import os
import pandas as pd
import base64
import json  # 用于处理 base64 解码和编码
import logging

# 获取日志器
logger = logging.getLogger(__name__)


class FaceRecognitionService:
    def __init__(self, app_config_data):
        self.app_config = app_config_data
        self.detector = None
        self.predictor = None
        self.face_reco_model = None
        self.features_known_list = []
        self.face_name_known_list = []


    def initialize_models(self):
        logger.info("正在加载 Dlib 人脸识别模型...")
        try:
            # 假设 data 文件夹在 backend 目录下，路径是相对于 backend
            # 如果你的 data 文件夹在项目根目录，需要调整路径为 '../data/data_dlib/...'
            dlib_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'data_dlib')
            features_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data',
                                             'features_all.csv')

            # 检查 Dlib 模型文件是否存在
            predictor_path = os.path.join(dlib_data_path, 'shape_predictor_68_face_landmarks.dat')
            reco_model_path = os.path.join(dlib_data_path, 'dlib_face_recognition_resnet_model_v1.dat')

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

    def _load_face_database(self, path_features_known_csv):
        """
        从 CSV 文件加载已知人脸特征和名字。
        """
        self.features_known_list = []
        self.face_name_known_list = []
        if os.path.exists(path_features_known_csv):
            try:
                csv_rd = pd.read_csv(path_features_known_csv, header=None)
                for i in range(csv_rd.shape[0]):
                    features_someone_arr = []
                    face_name_known_list_item = csv_rd.iloc[i][0]
                    # 处理姓名可能需要转换或映射
                    self.face_name_known_list.append(str(face_name_known_list_item))  # 确保姓名是字符串
                    for j in range(1, 129):
                        if pd.isna(csv_rd.iloc[i][j]) or str(csv_rd.iloc[i][j]) == '':
                            features_someone_arr.append(0.0)
                        else:
                            features_someone_arr.append(float(csv_rd.iloc[i][j]))
                    self.features_known_list.append(np.array(features_someone_arr, dtype=np.float64))
                logger.info(
                    f"人脸数据库 '{path_features_known_csv}' 加载完成，已包含 {len(self.features_known_list)} 张已知人脸。")
            except Exception as e:
                logger.error(f"加载人脸数据库 '{path_features_known_csv}' 失败: {e}", exc_info=True)
                self.features_known_list = []
                self.face_name_known_list = []
        else:
            logger.warning(f"人脸数据库文件 '{path_features_known_csv}' 未找到！请先运行特征提取脚本。")

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
            # 移除 "data:image/jpeg;base64," 前缀
            header, encoded_image = base64_image_data.split(',')

            # 解码 Base64 图像
            nparr = np.frombuffer(base64.b64decode(encoded_image), np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_np is None:
                logger.warning("无法解码图像数据。")
                return [{"status": "error", "message": "Invalid image data."}]

            # 将 BGR 转换为 RGB (dlib 需要 RGB)
            img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)

            faces = self.detector(img_rgb, 0)  # 0 代表不向上采样

            recognition_results = []
            if len(faces) > 0:
                for i, d in enumerate(faces):
                    # 提取人脸特征点
                    shape = self.predictor(img_rgb, d)
                    # 提取 128D 人脸特征
                    face_descriptor = self.face_reco_model.compute_face_descriptor(img_rgb, shape)
                    face_descriptor_np = np.array(face_descriptor)  # 转换为 numpy 数组以便计算

                    min_dist = float('inf')
                    recognized_name = "未知人员"

                    # 遍历已知人脸库进行比对
                    if self.features_known_list:
                        for j, known_feature in enumerate(self.features_known_list):
                            dist = self._return_euclidean_distance(face_descriptor_np, known_feature)
                            if dist < min_dist:
                                min_dist = dist
                                if min_dist < 0.4:  # 设置一个阈值，小于这个距离认为是同一个人
                                    recognized_name = self.face_name_known_list[j]
                                else:
                                    recognized_name = "陌生人"

                    recognition_results.append({
                        "face_id": i,
                        "name": recognized_name,
                        "distance": round(min_dist, 3) if min_dist != float('inf') else None,
                        "bbox": {"left": d.left(), "top": d.top(), "right": d.right(), "bottom": d.bottom()}
                    })
                    logger.info(f"检测到人脸: {recognized_name} (距离: {min_dist:.3f})")

            else:
                logger.info("未检测到人脸。")
                recognition_results.append({"name": "未检测到人脸", "status": "no_face"})

            return recognition_results

        except Exception as e:
            logger.error(f"人脸识别服务处理图像失败: {e}", exc_info=True)
            return [{"status": "error", "message": f"Processing error: {e}"}]