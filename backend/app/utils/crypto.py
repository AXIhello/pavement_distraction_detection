"""
AES加密解密工具模块
用于对人脸特征等敏感数据进行加密存储
"""
import os
import base64
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2
import logging

logger = logging.getLogger(__name__)

class AESEncryption:
    def __init__(self, key=None, salt=None):
        """
        初始化AES加密器
        Args:
            key: 加密密钥，如果为None则从环境变量获取
            salt: 盐值，如果为None则从环境变量获取
        """
        # 从环境变量获取密钥和盐值，如果没有则使用默认值（仅用于开发测试）
        self.key = key or os.environ.get('AES_KEY', 'your16bytekey12345678901234567890')
        self.salt = salt or os.environ.get('AES_SALT', 'yoursalt123456789012345678901234')
        
        # 确保密钥是bytes类型
        if isinstance(self.key, str):
            self.key = self.key.encode('utf-8')
        if isinstance(self.salt, str):
            self.salt = self.salt.encode('utf-8')
        
        # 生成32字节密钥和16字节IV
        self.derived_key = PBKDF2(self.key, self.salt, dkLen=32)
        self.iv = self.derived_key[:16]
    
    def encrypt_data(self, data: bytes) -> str:
        """
        加密数据
        Args:
            data: 要加密的字节数据
        Returns:
            加密后的base64字符串
        """
        try:
            cipher = AES.new(self.derived_key, AES.MODE_CBC, self.iv)
            ct_bytes = cipher.encrypt(pad(data, AES.block_size))
            return base64.b64encode(ct_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise
    
    def decrypt_data(self, enc_data: str) -> bytes:
        """
        解密数据
        Args:
            enc_data: 加密后的base64字符串
        Returns:
            解密后的字节数据
        """
        try:
            cipher = AES.new(self.derived_key, AES.MODE_CBC, self.iv)
            ct = base64.b64decode(enc_data)
            return unpad(cipher.decrypt(ct), AES.block_size)
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise
    
    def encrypt_numpy_array(self, array: np.ndarray) -> str:
        """
        加密numpy数组
        Args:
            array: numpy数组
        Returns:
            加密后的base64字符串
        """
        # 将numpy数组转换为字节
        array_bytes = array.astype(np.float32).tobytes()
        return self.encrypt_data(array_bytes)
    
    def decrypt_numpy_array(self, enc_data: str, shape: tuple = None) -> np.ndarray:
        """
        解密numpy数组
        Args:
            enc_data: 加密后的base64字符串
            shape: 数组形状，如果为None则假设是128维特征向量
        Returns:
            解密后的numpy数组
        """
        array_bytes = self.decrypt_data(enc_data)
        array = np.frombuffer(array_bytes, dtype=np.float32)
        
        # 如果指定了形状，则重塑数组
        if shape:
            array = array.reshape(shape)
        
        return array
    
    def encrypt_feature_vector(self, feature_vector: np.ndarray) -> str:
        """
        专门用于加密人脸特征向量（128维）
        Args:
            feature_vector: 128维人脸特征向量
        Returns:
            加密后的base64字符串
        """
        if feature_vector.shape != (128,):
            raise ValueError(f"特征向量维度错误，期望(128,)，实际{feature_vector.shape}")
        return self.encrypt_numpy_array(feature_vector)
    
    def decrypt_feature_vector(self, enc_data: str) -> np.ndarray:
        """
        专门用于解密人脸特征向量（128维）
        Args:
            enc_data: 加密后的base64字符串
        Returns:
            解密后的128维特征向量
        """
        return self.decrypt_numpy_array(enc_data, shape=(128,))

# 创建全局加密器实例
aes_encryption = AESEncryption() 