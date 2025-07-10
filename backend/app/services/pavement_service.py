# backend/app/services/pavement_service.py

from pathlib import Path
import torch
from PIL import Image
import io
import base64
import os
import numpy as np
from typing import List, Dict

# 类别ID到中文标签的映射
id2label = {
    'D00': '横向裂缝',
    'D10': '纵向裂缝',
    'D20': '龟裂',
    'D40': '车辙/颠簸/坑洼/松散',
    'D43': '斑马线模糊',
    'D44': '白线模糊',
    'D50': '井盖'
}

# 模型文件路径
model_path = Path('data/weights/road_damage.pt')

# 尝试加载模型
model = None
if not model_path.exists():
    print(f"[ERROR] 模型文件不存在: {model_path}")
    print(f"当前工作目录: {os.getcwd()}") # 保留此行以方便排查模型路径问题
else:
    print(f"[INFO] 找到模型文件: {model_path}")
    try:
        print(" [INFO] 正在加载YOLOv5官方推理接口模型...")
        # 使用 torch.hub.load 加载自定义模型
        model = torch.hub.load('yolov5', 'custom', path=str(model_path),source='local')
        model.conf = 0.25 # 设置置信度阈值
        print("[SUCCESS] YOLOv5模型加载成功（ultralytics官方接口）")
    except Exception as e:
        print(f"[ERROR] 模型加载失败: {str(e)}")
        model = None


def detect_single_image(base64_image: str) -> Dict:
    """
    对单帧 Base64 图像进行检测
    :param base64_image: str Base64编码的图像
    :return: Dict 检测结果，包含状态、检测对象和标注后的图像
    """
    # 检查模型是否加载成功
    if model is None:
        print("[ERROR] 模型未加载，无法进行检测")
        return {
            'status': 'error',
            'message': '模型未加载，无法进行检测',
            'detections': [],
            'annotated_image': None
        }

    try:
        # 验证Base64格式
        if not base64_image.startswith('data:image'):
            raise ValueError("不是有效的 Base64 图像格式")

        # 解码图像
        _, encoded = base64_image.split(',', 1)
        image_bytes = base64.b64decode(encoded)

        # 使用PIL加载图像并转换为RGB
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # image = image.resize((640, 640))  # 移除强制resize，保持原图分辨率
        image_np = np.array(image) # 转换为NumPy数组供YOLOv5模型使用

        # 执行检测
        output = model(image_np)

        # 解析检测结果
        df = output.pandas().xyxy[0]

        detections = []
        for _, row in df.iterrows():
            label_key = row['name']
            # 修改模型内部的类别名为中文，以便渲染时显示中文标签
            output.names[row['class']] = id2label.get(label_key, label_key)

            detections.append({
                'class': id2label.get(label_key, label_key),
                'confidence': round(float(row['confidence']), 3),
                'bbox': [round(float(row['xmin']), 2), round(float(row['ymin']), 2),
                         round(float(row['xmax']), 2), round(float(row['ymax']), 2)]
            })

        # 渲染图像（YOLOv5的render方法会使用更新后的中文类别名）
        rendered = output.render()[0]  # 返回的是ndarray (BGR格式)
        image_pil = Image.fromarray(rendered)  # 正确，不用转换


        # 将标注后的图像转换为Base64编码
        buffered = io.BytesIO()
        image_pil.save(buffered, format="JPEG")

        annotated_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        result = {
            'status': 'success',
            'detections': detections,
            'annotated_image': annotated_image_base64
        }
        return result

    except Exception as e:
        print(f" [ERROR] 检测失败: {str(e)}") # 保留此行，用于错误报告
        return {
            'status': 'error',
            'message': f'检测失败: {str(e)}',
            'detections': [],
            'annotated_image': None
        }


def detect_batch_images(base64_images: List[str]) -> List[Dict]:
    """
    对多帧 Base64 图像进行检测，并返回标注后的 Base64 图像
    :param base64_images: List[str] Base64编码的图像列表
    :return: List[Dict] 每帧的检测结果
    """
    results = []

    # 检查模型是否加载成功
    if model is None:
        print("[ERROR] 模型未加载，无法进行批量检测")
        return [{
            'frame_index': i,
            'detections': [],
            'image_base64': None,
            'status': 'error',
            'message': '模型未加载，无法进行批量检测'
        } for i in range(len(base64_images))]

    for i, base64_str in enumerate(base64_images):
        try:
            if not base64_str.startswith('data:image'):
                raise ValueError(f"第 {i} 帧不是有效的 Base64 图像。")

            _, encoded = base64_str.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            # image = image.resize((640, 640))  # 移除强制resize，保持原图分辨率
            image_np = np.array(image)

            detections = []
            output = model(image_np)
            df = output.pandas().xyxy[0]

            for _, row in df.iterrows():
                label_key = row['name']
                output.names[row['class']] = id2label.get(label_key, label_key)

                detections.append({
                    'class': id2label.get(label_key, label_key),
                    'confidence': round(float(row['confidence']), 3),
                    'bbox': [round(float(row['xmin']), 2), round(float(row['ymin']), 2),
                             round(float(row['xmax']), 2), round(float(row['ymax']), 2)]
                })

            rendered = output.render()[0]
            image_pil = Image.fromarray(rendered[..., ::-1])

            buffered = io.BytesIO()
            image_pil.save(buffered, format="JPEG")
            image_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

            results.append({
                'frame_index': i,
                'detections': detections,
                'image_base64': image_base64,
                'status': 'success'
            })

        except Exception as e:
            print(f"[ERROR] 批量检测中第 {i} 帧处理失败: {str(e)}")
            results.append({
                'frame_index': i,
                'detections': [],
                'image_base64': None,
                'status': 'error',
                'message': f'第{i}帧处理失败: {str(e)}'
            })

    return results
