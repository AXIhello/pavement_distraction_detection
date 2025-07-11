# 数据库模型定义
# app/models
from datetime import datetime
from ..extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128))
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
    
# 记录一次路害告警视频上传的信息
class AlertVideo(db.Model):
    __tablename__ = 'alert_videos'

    id = db.Column(db.Integer, primary_key=True)
    video_name = db.Column(db.String(255), nullable=False)  # 原始视频名称
    user_id = db.Column(db.Integer, nullable=True)  # 如果需要支持用户关联
    save_dir = db.Column(db.String(512), nullable=False)  # 病害图像保存目录
    total_frames = db.Column(db.Integer, nullable=False)  # 视频总帧数
    alert_frame_count = db.Column(db.Integer, nullable=False)  # 病害帧数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间

    alert_frames = db.relationship('AlertFrame', backref='video', cascade='all, delete-orphan')

# 记录一次路害视频中的告警一帧
class AlertFrame(db.Model):
    __tablename__ = 'alert_frames'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('alert_videos.id'), nullable=False)
    frame_index = db.Column(db.Integer, nullable=False)  # 第几帧
    disease_type = db.Column(db.String(100), nullable=False)  # 病害类型
    confidence = db.Column(db.Float, nullable=False)  # 检测置信度（选第一个目标）
    image_path = db.Column(db.String(512), nullable=False)  # 病害图像路径（带标注图）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)