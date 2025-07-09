# backend/app/services/pavement_service.py

from pathlib import Path
import torch
from PIL import Image
import io
import base64
import os
import numpy as np

id2label = {
    'D00': '横向裂缝',
    'D10': '纵向裂缝',
    'D20': '龟裂',
    'D40': '车辙/颠簸/坑洼/松散',
    'D43': '斑马线模糊',
    'D44': '白线模糊',
    'D50': '井盖'
}

model_path = Path('data/weights/road_damage.pt')

# 检查模型文件是否存在
if not model_path.exists():
    print(f"❌ [ERROR] 模型文件不存在: {model_path}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"绝对路径: {model_path.absolute()}")
    model = None
else:
    print(f"✅ [INFO] 找到模型文件: {model_path}")
    try:
        print("🔄 [INFO] 正在加载YOLOv5官方推理接口模型...")
        # 只用 model，不要用 model.model
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path))
        model.conf = 0.25
        print("✅ [SUCCESS] YOLOv5模型加载成功（ultralytics官方接口）")
    except Exception as e:
        print(f"❌ [ERROR] 模型加载失败: {str(e)}")
        model = None


def detect_single_image(base64_image):
    """
    对单帧 Base64 图像进行检测
    :param base64_image: str Base64编码的图像
    :return: Dict 检测结果
    """
    print("🔍 [DEBUG] detect_single_image 函数开始执行")

    # 首先检查模型是否加载成功
    if model is None:
        print("❌ [ERROR] 模型未加载，无法进行检测")
        return {
            'status': 'error',
            'message': '模型未加载，无法进行检测',
            'detections': [],
            'annotated_image': None
        }

    try:
        # 验证Base64格式
        print(f"🔍 [DEBUG] 检查图像格式，数据长度: {len(base64_image)}")
        if not base64_image.startswith('data:image'):
            print("❌ [ERROR] 不是有效的 Base64 图像格式")
            raise ValueError("不是有效的 Base64 图像格式")

        print("✅ [DEBUG] Base64 格式验证通过")

        # 解码图像
        header, encoded = base64_image.split(',', 1)
        print(f"🔍 [DEBUG] 图像头: {header}")
        image_bytes = base64.b64decode(encoded)
        print(f"🔍 [DEBUG] 解码后字节长度: {len(image_bytes)}")

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((640, 640))  # 强制resize到640x640
        image_np = np.array(image)
        print(f"🔍 [DEBUG] 图像尺寸: {image.size}")

        # 执行检测
        print("🔍 [DEBUG] 开始模型推理...")
        output = model(image_np)
        print("✅ [DEBUG] 模型推理完成")

        df = output.pandas().xyxy[0]
        print(f"🔍 [DEBUG] 检测结果数量: {len(df)}")

        if len(df) > 0:
            print("🔍 [DEBUG] 检测结果详情:")
            for i, (_, row) in enumerate(df.iterrows()):
                print(f"  {i + 1}. 类别: {row['name']}, 置信度: {row['confidence']:.3f}")

        detections = []
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

        print("🔍 [DEBUG] 开始渲染图像...")
        # 渲染图像（中文类别已通过 output.names 替换）
        rendered = output.render()[0]  # ndarray (BGR)
        image_pil = Image.fromarray(rendered[..., ::-1])  # 转为 RGB
        print("✅ [DEBUG] 图像渲染完成")

        # 转换为base64
        print("🔍 [DEBUG] 转换为base64...")
        buffered = io.BytesIO()
        image_pil.save(buffered, format="JPEG")
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
        print(f"❌ [ERROR] 检测失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': f'检测失败: {str(e)}',
            'detections': [],
            'annotated_image': None
        }


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
        image = image.resize((640, 640))  # 强制resize到640x640
        image_np = np.array(image)

        detections = []
        try:
            output = model(image_np)
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