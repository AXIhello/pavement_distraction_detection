# backend/app/services/pavement_service.py

from pathlib import Path
import torch
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import numpy as np
from typing import List, Dict

from ..services.alert_service import save_alert_frame, update_alert_video, create_alert_video
from datetime import datetime
from ..extensions import db

# 类别ID到中文标签的映射
id2label = {
    'D00': '纵向裂缝',
    'D10': '横向裂缝',
    'D20': '龟裂',
    'D40': '车辙/颠簸/坑洼/松散',
    'D43': '斑马线模糊',
    'D44': '白线模糊',
    'D50': '井盖'
}

# 类别颜色映射（RGB）
label2color = {
    '纵向裂缝': (255, 0, 0),
    '横向裂缝': (0, 255, 0),
    '龟裂': (0, 0, 255),
    '车辙/颠簸/坑洼/松散': (255, 165, 0),
    '斑马线模糊': (128, 0, 128),
    '白线模糊': (0, 255, 255),
    '井盖': (255, 192, 203),
}

model_path = Path('data/weights/road_damage.pt')
model = None
if not model_path.exists():
    print(f"[ERROR] 模型文件不存在: {model_path}")
    print(f"当前工作目录: {os.getcwd()}")
else:
    print(f"[INFO] 找到模型文件: {model_path}")
    try:
        print(" [INFO] 正在加载YOLOv5官方推理接口模型...")
        model = torch.hub.load('yolov5', 'custom', path=str(model_path), source='local')
        model.conf = 0.30
        print("[SUCCESS] YOLOv5模型加载成功（ultralytics官方接口）")
    except Exception as e:
        print(f"[ERROR] 模型加载失败: {str(e)}")
        model = None

def draw_detections(image, detections):
    draw = ImageDraw.Draw(image)
    for det in detections:
        bbox = det['bbox']
        label = det['class']
        conf = det['confidence']
        color = label2color.get(label, (255, 0, 0))
        draw.rectangle(bbox, outline=color, width=2)
        text = f"{label} {conf:.2f}"
        from pathlib import Path
        font_path = Path("data/SimHei.ttf")
        try:
            font = ImageFont.truetype(str(font_path), 16)
        except:
            font = None

        x, y = bbox[0], bbox[1] - 20 if bbox[1] - 20 > 0 else bbox[1] + 2
        draw.text((x, y), text, fill=color, font=font)
    return image

def detect_single_image(base64_image: str) -> Dict:
    if model is None:
        return {'status': 'error', 'message': '模型未加载，无法进行检测', 'detections': [], 'annotated_image': None}

    try:
        if not base64_image.startswith('data:image'):
            raise ValueError("不是有效的 Base64 图像格式")

        _, encoded = base64_image.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        orig_w, orig_h = image.size
        image_resized = image.resize((640, 640))
        image_np = np.array(image_resized)

        output = model(image_np)
        df = output.pandas().xyxy[0]
        w_scale = orig_w / 640
        h_scale = orig_h / 640

        detections = []
        for _, row in df.iterrows():
            label_key = row['name']
            output.names[row['class']] = id2label.get(label_key, label_key)
            xmin_r = row['xmin'] * w_scale
            ymin_r = row['ymin'] * h_scale
            xmax_r = row['xmax'] * w_scale
            ymax_r = row['ymax'] * h_scale
            detections.append({
                'class': id2label.get(label_key, label_key),
                'confidence': round(float(row['confidence']), 3),
                'bbox': [round(xmin_r, 2), round(ymin_r, 2), round(xmax_r, 2), round(ymax_r, 2)]
            })

        annotated = draw_detections(image.copy(), detections)
        buffered = io.BytesIO()
        annotated.save(buffered, format="JPEG")
        annotated_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        return {'status': 'success', 'detections': detections, 'annotated_image': annotated_image_base64}

    except Exception as e:
        print(f"[ERROR] 检测失败: {str(e)}")
        return {'status': 'error', 'message': f'检测失败: {str(e)}', 'detections': [], 'annotated_image': None}

def detect_batch_images(base64_images: List[str]) -> List[Dict]:
    results = []
    if model is None:
        return [{'frame_index': i, 'detections': [], 'image_base64': None, 'status': 'error', 'message': '模型未加载'} for i in range(len(base64_images))]

    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    save_dir = Path(f'data/alert_videos/video_{timestamp}')
    save_dir.mkdir(parents=True, exist_ok=True)
    video_id = create_alert_video('road', f'video_{timestamp}', str(save_dir), len(base64_images), 0, None)
    alert_count = 0

    for i, base64_str in enumerate(base64_images):
        try:
            if not base64_str.startswith('data:image'):
                raise ValueError(f"第 {i} 帧不是有效的 Base64 图像。")

            _, encoded = base64_str.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            orig_w, orig_h = image.size
            image_resized = image.resize((640, 640))
            image_np = np.array(image_resized)
            w_scale = orig_w / 640
            h_scale = orig_h / 640

            output = model(image_np)
            df = output.pandas().xyxy[0]
            detections = []

            for _, row in df.iterrows():
                label_key = row['name']
                output.names[row['class']] = id2label.get(label_key, label_key)
                xmin_r = row['xmin'] * w_scale
                ymin_r = row['ymin'] * h_scale
                xmax_r = row['xmax'] * w_scale
                ymax_r = row['ymax'] * h_scale
                detections.append({
                    'class': id2label.get(label_key, label_key),
                    'confidence': round(float(row['confidence']), 3),
                    'bbox': [round(xmin_r, 2), round(ymin_r, 2), round(xmax_r, 2), round(ymax_r, 2)]
                })

            annotated = draw_detections(image.copy(), detections)
            buffered = io.BytesIO()
            annotated.save(buffered, format="JPEG")
            image_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

            if detections:
                alert_count += 1
                first = detections[0]
                save_alert_frame('road', video_id, i, image_base64, first['confidence'], first['class'], first['bbox'])

            results.append({'frame_index': i, 'detections': detections, 'image_base64': image_base64})

        except Exception as e:
            print(f"[ERROR] 批量检测中第 {i} 帧处理失败: {str(e)}")
            results.append({
                'frame_index': i,
                'detections': [],
                'image_base64': None,
                'status': 'error',
                'message': f'第{i}帧处理失败: {str(e)}'
            })

    update_alert_video('road', video_id, alert_count)
    return results
