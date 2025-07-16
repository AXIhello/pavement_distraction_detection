# backend/app/services/alert_service.py
from pathlib import Path
import base64
import io
from PIL import Image
from datetime import datetime
from app.extensions import db
from app.core.models import AlertVideo, AlertFrame, FaceAlertFrame

# 还未设计人脸告警相关的模型

def create_alert_video(db_type: str, video_name: str, save_dir: str, total_frames: int, alert_frame_count: int, user_id: int = None) -> int:
    if db_type == 'road':
        VideoModel = AlertVideo
    else:
        raise ValueError(f"不支持的告警类型: {db_type}")

    video = VideoModel(
        video_name=video_name,
        save_dir=save_dir,
        total_frames=total_frames,
        alert_frame_count=alert_frame_count,
        created_at=datetime.utcnow()
    )
    db.session.add(video)
    db.session.commit()
    return video.id

def save_alert_frame(db_type: str, image_base64: str,confidence: float,video_id: int = 0, frame_index: int = 0,  disease_type: str = None, bboxes: list = None,save_dir0: str = None) -> str:
    if db_type == 'road':
        VideoModel = AlertVideo
        FrameModel = AlertFrame

        video = VideoModel.query.get(video_id)
        if not video:
            raise ValueError(f"告警视频ID {video_id} 不存在")
        
        save_dir = Path(video.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = f"frame_{frame_index:05d}.jpg"
        save_path = save_dir / filename

    elif db_type == 'face':
        FrameModel = FaceAlertFrame
        save_path = Path(save_dir0)
    else:
        raise ValueError(f"不支持的告警类型: {db_type}")

    # 保存图像
    # 去掉 data:image/jpeg;base64, 这样的前缀（如果有的话）
    if image_base64.startswith('data:image'):
        image_base64 = image_base64.split(',', 1)[1]

    # 解码 base64 字符串为字节数据
    image_data = base64.b64decode(image_base64)

    # 使用 Pillow 打开图像
    image = Image.open(io.BytesIO(image_data))

    # 保存到本地
    image.save(save_path)
    print(f"图像已保存到：{save_path}")

    if db_type == 'road':
        alert_frame = FrameModel(
        video_id=video_id,
        frame_index=frame_index,
        disease_type=disease_type or "未知",
        confidence=confidence,
        image_path=str(save_path),
        created_at=datetime.utcnow()
    )
    elif db_type == 'face':
        alert_frame = FrameModel(
        alert_type=disease_type or "未知",  
        confidence=confidence,
        image_path=str(save_path),
        created_at=datetime.utcnow()
    )

    db.session.add(alert_frame)
    db.session.commit()

    return str(save_path)

def update_alert_video(db_type: str, video_id: int, alert_frame_count: int):
    if db_type == 'road':
        VideoModel = AlertVideo
    else:
        raise ValueError(f"不支持的告警类型: {db_type}")

    video = VideoModel.query.get(video_id)
    if not video:
        raise ValueError(f"告警视频ID {video_id} 不存在")

    video.alert_frame_count = alert_frame_count
    db.session.commit()

#更新视频帧数量和病害帧数量
def update_alert_video_frame_count(db_type: str, video_id: int, total_frames: int, alert_frame_count: int):
    if db_type == 'road':
        VideoModel = AlertVideo
    else:
        raise ValueError(f"不支持的告警类型: {db_type}")

    video = VideoModel.query.get(video_id)
    if not video:
        raise ValueError(f"告警视频ID {video_id} 不存在")

    video.total_frames = total_frames
    video.alert_frame_count = alert_frame_count
    db.session.commit()
