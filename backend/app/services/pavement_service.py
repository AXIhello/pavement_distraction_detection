# backend/app/services/pavement_service.py

import base64
import io
from pathlib import Path

import torch
from PIL import Image

# 病害类别映射（模型输出类别 -> 中文名）
id2label = {
    'D00': '横向裂缝',
    'D10': '纵向裂缝',
    'D20': '龟裂',
    'D40': '车辙/颠簸/坑洼/松散',
    'D43': '斑马线模糊',
    'D44': '白线模糊',
    'D50': '井盖'
}

# 加载 YOLOv5 模型（全局只加载一次）
model_path = Path('backend/data/weights/road_damage.pt')
model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path), force_reload=False)
model.conf = 0.25  # 置信度阈值，可调


def detect_pavement_damage(base64_image_str: str):
    """
    执行推理，返回检测结果列表
    :param base64_image_str: 前端传来的 Base64 图片字符串（带data:image开头）
    :return: List[Dict]
    """
    if not base64_image_str.startswith('data:image'):
        raise ValueError("Base64 字符串格式错误")

    header, encoded = base64_image_str.split(',', 1)
    image_bytes = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results = model(image, size=640)
    df = results.pandas().xyxy[0]  # DataFrame

    result_list = []
    for _, row in df.iterrows():
        label_key = row['name']
        result_list.append({
            'class': id2label.get(label_key, label_key),
            'confidence': round(float(row['confidence']), 3),
            'bbox': [round(float(row['xmin']), 2), round(float(row['ymin']), 2),
                     round(float(row['xmax']), 2), round(float(row['ymax']), 2)]
        })

    return result_list
