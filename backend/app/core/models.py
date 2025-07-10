# 数据库模型定义
# app/models
from datetime import datetime
from ..extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FaceFeature(db.Model):
    """
    人脸特征数据库模型
    存储加密后的人脸特征向量
    """
    __tablename__ = 'face_features'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, index=True)  # 人名
    feature_encrypted = db.Column(db.Text, nullable=False)  # 加密后的特征向量（base64字符串）
    feature_count = db.Column(db.Integer, default=1)  # 该人的特征图片数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FaceFeature {self.name}>'
    
    @classmethod
    def get_by_name(cls, name):
        """根据姓名获取人脸特征记录"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_all_features(cls):
        """获取所有人脸特征记录"""
        return cls.query.all()
    
    @classmethod
    def delete_by_name(cls, name):
        """根据姓名删除人脸特征记录"""
        record = cls.get_by_name(name)
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False