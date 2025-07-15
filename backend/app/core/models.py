# 数据库模型定义
# app/models
from datetime import datetime
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from datetime import datetime

class LogEntry(db.Model):
    __tablename__ = 'log_entries'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20))
    message = db.Column(db.Text)
    pathname = db.Column(db.String(256))
    lineno = db.Column(db.Integer)
    module = db.Column(db.String(128))

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "message": self.message,
            "pathname": self.pathname,
            "lineno": self.lineno,
            "module": self.module
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='admin')  # 用户角色（如 admin, user 等）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'email': self.email
        }       

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='face_features')
    image_path = db.Column(db.String(512))
    
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
    save_dir = db.Column(db.String(512), nullable=False)  # 病害图像保存目录
    total_frames = db.Column(db.Integer, nullable=False)  # 视频总帧数
    alert_frame_count = db.Column(db.Integer, nullable=False)  # 病害帧数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间

    alert_frames = db.relationship('AlertFrame', backref='video', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'video_name': self.video_name,
            'save_dir': self.save_dir,
            'disease_type':'未知',
            'total_frames': self.total_frames,
            'alert_frame_count': self.alert_frame_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

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

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'frame_index': self.frame_index,
            'disease_type': self.disease_type,
            'confidence': self.confidence,
            'image_path': self.image_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 人脸告警帧表
class FaceAlertFrame(db.Model):
    __tablename__ = 'face_alert_frames'

    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(512), nullable=False)
    alert_type = db.Column(db.String(128), nullable=False)  # 告警类型（如陌生人、伪人等）
    confidence = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
                'id': self.id,                                              
                'image_path': self.image_path,                                                
                'alert_type': self.alert_type,                                                          
                'confidence': self.confidence,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }                        

# -------- 用户相关操作 --------

def find_user_by_username(username):
    return User.query.filter_by(username=username).first()

def find_user_by_email(email):
    return User.query.filter_by(email=email).first()

def create_user(username=None, email=None, password=None):
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user