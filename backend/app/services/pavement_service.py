# backend/app/services/pavement_service.py

from pathlib import Path
import torch
from PIL import Image
import io
import base64

id2label = {
    'D00': '横向裂缝',
    'D10': '纵向裂缝',
    'D20': '龟裂',
    'D40': '车辙/颠簸/坑洼/松散',
    'D43': '斑马线模糊',
    'D44': '白线模糊',
    'D50': '井盖'
}

model_path = Path('backend/data/weights/road_damage.pt')
model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path), force_reload=False)
model.conf = 0.25


def detect_batch_images(base64_images):
    """
    对多帧 Base64 图像进行检测，并返回标注后的 Base64 图像
    :param base64_images: List[str]
    :return: List[Dict] 每帧检测结果
    """
    results = []

    for i, base64_str in enumerate(base64_images):
        if not base64_str.startswith('data:image'):
            raise ValueError(f"第 {i} 帧不是有效的 Base64 图像。")

        header, encoded = base64_str.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        detections = []
        try:
            output = model(image, size=640)
            df = output.pandas().xyxy[0]

            for _, row in df.iterrows():
                label_key = row['name']
                # 修改模型内的类别名为中文（这一步用于渲染）
                output.names[row['class']] = id2label.get(label_key, label_key)

                detections.append({
                    'class': id2label.get(label_key, label_key),
                    'confidence': round(float(row['confidence']), 3),
                    'bbox': [round(float(row['xmin']), 2), round(float(row['ymin']), 2),
                             round(float(row['xmax']), 2), round(float(row['ymax']), 2)]
                })

            # 渲染图像（中文类别已通过 output.names 替换）
            rendered = output.render()[0]  # ndarray (BGR)
            image_pil = Image.fromarray(rendered[..., ::-1])  # 转为 RGB

            buffered = io.BytesIO()
            image_pil.save(buffered, format="JPEG")
            image_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

            results.append({
                'frame_index': i,
                'detections': detections,
                'image_base64': image_base64
            })

        except Exception as e:
            results.append({
                'frame_index': i,
                'detections': [{'error': f'第{i}帧处理失败: {str(e)}'}],
                'image_base64': None
            })

    return results
