# backend/app/services/pavement_service.py

from pathlib import Path
import torch
from PIL import Image
import io
import base64
import os
import numpy as np
from typing import List, Dict

from ..services.alert_service import save_alert_frame, update_alert_video, create_alert_video
from datetime import datetime
from app.extensions import db


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
        model.conf = 0.30 # 设置置信度阈值
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
        orig_w, orig_h = image.size  # 记录原始尺寸
        image_resized = image.resize((640, 640))
        image_np = np.array(image_resized)

        # 执行检测
        output = model(image_np)
        df = output.pandas().xyxy[0]

        w_scale = orig_w / 640
        h_scale = orig_h / 640

        detections = []
        for _, row in df.iterrows():
            label_key = row['name']
            # 修改模型内的类别名为中文（这一步用于渲染）
            output.names[row['class']] = id2label.get(label_key, label_key)

            # 坐标还原
            xmin_r = row['xmin'] * w_scale
            ymin_r = row['ymin'] * h_scale
            xmax_r = row['xmax'] * w_scale
            ymax_r = row['ymax'] * h_scale

            detections.append({
                'class': id2label.get(label_key, label_key),
                'confidence': round(float(row['confidence']), 3),
                'bbox': [round(xmin_r, 2), round(ymin_r, 2), round(xmax_r, 2), round(ymax_r, 2)]
            })

        print("🔍 [DEBUG] 开始在原图上渲染标注...")
        # 在原图上绘制还原后的检测框
        from PIL import ImageDraw
        image_draw = image.copy()
        draw = ImageDraw.Draw(image_draw)
        for det in detections:
            bbox = det['bbox']
            draw.rectangle(bbox, outline='red', width=2)
        print("✅ [DEBUG] 原图渲染完成")

        # 转换为base64
        print("🔍 [DEBUG] 转换为base64...")
        buffered = io.BytesIO()
        image_draw.save(buffered, format="JPEG")
        annotated_image_base64 = base64.b64encode(buffered.getvalue()).decode()
        print(f"✅ [DEBUG] Base64转换完成，长度: {len(annotated_image_base64)}")

        result = {
            'status': 'success',
            'detections': detections,
            'annotated_image': annotated_image_base64
        }

        print(f"🎉 [SUCCESS] 检测完成，返回结果: status={result['status']}, 检测数量={len(detections)}")
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
    
    # 1️. 自动生成保存路径
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    save_dir = Path(f'data/alert_videos/video_{timestamp}')
    save_dir.mkdir(parents=True, exist_ok=True)

    # 2. 路面病害告警
    video_id = create_alert_video('road',f'video_{timestamp}', str(save_dir), len(base64_images), 0, None)

    alert_count = 0 

    for i, base64_str in enumerate(base64_images):
        try:
            if not base64_str.startswith('data:image'):
                raise ValueError(f"第 {i} 帧不是有效的 Base64 图像。")

            _, encoded = base64_str.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            orig_w, orig_h = image.size  # 记录原始尺寸
            image_resized = image.resize((640, 640))
            image_np = np.array(image_resized)
            w_scale = orig_w / 640
            h_scale = orig_h / 640

            detections = []
            output = model(image_np)
            df = output.pandas().xyxy[0]

            for _, row in df.iterrows():
                label_key = row['name']
                # 修改模型内的类别名为中文（这一步用于渲染）
                output.names[row['class']] = id2label.get(label_key, label_key)

                # 坐标还原
                xmin_r = row['xmin'] * w_scale
                ymin_r = row['ymin'] * h_scale
                xmax_r = row['xmax'] * w_scale
                ymax_r = row['ymax'] * h_scale

                detections.append({
                    'class': id2label.get(label_key, label_key),
                    'confidence': round(float(row['confidence']), 3),
                    'bbox': [round(xmin_r, 2), round(ymin_r, 2), round(xmax_r, 2), round(ymax_r, 2)]
                })

            # 在原图上绘制还原后的检测框
            from PIL import ImageDraw
            image_draw = image.copy()
            draw = ImageDraw.Draw(image_draw)
            for det in detections:
                bbox = det['bbox']
                draw.rectangle(bbox, outline='red', width=2)

            buffered = io.BytesIO()
            image_draw.save(buffered, format="JPEG")
            image_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

            # 3️. 有检测结果就保存图像 & 写入 AlertFrame
            # 如果一帧有多个目标，只保存第一个目标的置信度和类别？
            if detections:
                alert_count += 1
                save_alert_frame('road',video_id, i, image_base64, detections[0].confidences, detections[0].class_name,detections[0].bbox)

            results.append({
                'frame_index': i,
                'detections': detections,
                'image_base64': image_base64
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

    # 4️. 更新告警帧数量、提交数据库
    update_alert_video('road',video_id, alert_count)


    return results
