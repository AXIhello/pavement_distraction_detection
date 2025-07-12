"""
人脸特征数据库服务
处理人脸特征的加密存储和解密读取
"""
import numpy as np
import logging
from typing import List, Optional, Tuple
from ..core.models import FaceFeature
from ..extensions import db
from ..utils.crypto import aes_encryption

logger = logging.getLogger(__name__)

class FaceDatabaseService:
    """人脸特征数据库服务类"""
    
    @staticmethod
    def save_feature(name: str, feature_vector: np.ndarray) -> bool:
        """
        保存加密后的人脸特征到数据库
        如果该人已存在特征，则计算新旧特征的平均值
        Args:
            name: 人名
            feature_vector: 128维人脸特征向量
        Returns:
            是否保存成功
        """
        try:
            # 检查是否已存在该人的记录
            existing_record = FaceFeature.get_by_name(name)
            
            if existing_record:
                # 如果已存在，计算新旧特征的平均值
                old_feature = aes_encryption.decrypt_feature_vector(existing_record.feature_encrypted)
                # 计算平均值
                averaged_feature = (old_feature + feature_vector) / 2.0
                # 加密新的平均特征向量
                encrypted_feature = aes_encryption.encrypt_feature_vector(averaged_feature)
                
                # 更新现有记录
                existing_record.feature_encrypted = encrypted_feature
                existing_record.feature_count += 1
                existing_record.updated_at = db.func.now()
                logger.info(f"更新 {name} 的人脸特征（第 {existing_record.feature_count} 张照片），使用平均值")
            else:
                # 创建新记录
                encrypted_feature = aes_encryption.encrypt_feature_vector(feature_vector)
                new_record = FaceFeature(
                    name=name,
                    feature_encrypted=encrypted_feature,
                    feature_count=1
                )
                db.session.add(new_record)
                logger.info(f"新增 {name} 的人脸特征（第1张照片）")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存人脸特征失败: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    @staticmethod
    def get_feature(name: str) -> Optional[np.ndarray]:
        """
        从数据库获取并解密人脸特征
        Args:
            name: 人名
        Returns:
            解密后的128维特征向量，如果不存在则返回None
        """
        try:
            record = FaceFeature.get_by_name(name)
            if not record:
                logger.warning(f"未找到 {name} 的人脸特征记录")
                return None
            
            # 解密特征向量
            feature_vector = aes_encryption.decrypt_feature_vector(record.feature_encrypted)
            logger.info(f"成功获取 {name} 的人脸特征")
            return feature_vector
            
        except Exception as e:
            logger.error(f"获取人脸特征失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_all_features() -> List[Tuple[str, np.ndarray]]:
        """
        获取所有加密的人脸特征
        Returns:
            包含(姓名, 特征向量)元组的列表
        """
        try:
            records = FaceFeature.get_all_features()
            features = []
            
            for record in records:
                try:
                    feature_vector = aes_encryption.decrypt_feature_vector(record.feature_encrypted)
                    features.append((record.name, feature_vector))
                except Exception as e:
                    logger.error(f"解密 {record.name} 的特征失败: {e}")
                    continue
            
            logger.info(f"成功获取 {len(features)} 个人脸特征")
            return features
            
        except Exception as e:
            logger.error(f"获取所有人脸特征失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def delete_feature(name: str) -> bool:
        """
        删除指定人的人脸特征
        Args:
            name: 人名
        Returns:
            是否删除成功
        """
        try:
            success = FaceFeature.delete_by_name(name)
            if success:
                logger.info(f"成功删除 {name} 的人脸特征")
            else:
                logger.warning(f"未找到 {name} 的人脸特征记录")
            return success
            
        except Exception as e:
            logger.error(f"删除人脸特征失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_feature_count(name: str) -> int:
        """
        获取指定人的特征图片数量
        Args:
            name: 人名
        Returns:
            特征图片数量
        """
        try:
            record = FaceFeature.get_by_name(name)
            return record.feature_count if record else 0
        except Exception as e:
            logger.error(f"获取特征数量失败: {e}")
            return 0
    
    @staticmethod
    def get_all_names() -> List[str]:
        """
        获取所有已注册的人名
        Returns:
            人名列表
        """
        try:
            records = FaceFeature.get_all_features()
            return [record.name for record in records]
        except Exception as e:
            logger.error(f"获取所有人名失败: {e}")
            return []
    
    @staticmethod
    def update_feature(name: str, feature_vector: np.ndarray) -> bool:
        """
        更新指定人的人脸特征
        Args:
            name: 人名
            feature_vector: 新的128维特征向量
        Returns:
            是否更新成功
        """
        try:
            record = FaceFeature.get_by_name(name)
            if not record:
                logger.warning(f"未找到 {name} 的记录，无法更新")
                return False
            
            # 加密新的特征向量
            encrypted_feature = aes_encryption.encrypt_feature_vector(feature_vector)
            
            # 更新记录
            record.feature_encrypted = encrypted_feature
            record.updated_at = db.func.now()
            
            db.session.commit()
            logger.info(f"成功更新 {name} 的人脸特征")
            return True
            
        except Exception as e:
            logger.error(f"更新人脸特征失败: {e}", exc_info=True)
            db.session.rollback()
            return False 