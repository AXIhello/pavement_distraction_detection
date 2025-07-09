# backend/app/api/pavement_detection.py

from flask_restx import Namespace, Resource, fields
from ..services.pavement_service import detect_batch_images, detect_single_image

ns = Namespace('pavement_detection', description='路面病害检测相关操作')

# 保留原有的批量检测 API
parser = ns.parser()
parser.add_argument(
    'images', type=str, action='split', required=True, location='form',
    help='一组Base64编码的图片字符串，用英文逗号分隔'
)

detection_result_item_model = ns.model('DetectionResultItem', {
    'class': fields.String,
    'confidence': fields.Float,
    'bbox': fields.List(fields.Float),
    'error': fields.String(required=False)
})

frame_result_model = ns.model('FrameResult', {
    'frame_index': fields.Integer,
    'detections': fields.List(fields.Nested(detection_result_item_model))
})

detection_response_model = ns.model('DetectionResponse', {
    'status': fields.String,
    'message': fields.String,
    'frames': fields.List(fields.Nested(frame_result_model))
})


@ns.route('/analyze_video')
class DetectPavementBatch(Resource):
    @ns.doc('多帧路面病害检测')
    @ns.expect(parser)
    @ns.marshal_with(detection_response_model)
    @ns.response(400, '无效的请求数据')
    @ns.response(500, '服务器内部错误')
    def post(self):
        """
        对一组路面图像（Base64编码）执行病害检测
        """
        args = parser.parse_args()
        images = args['images']

        if not isinstance(images, list) or len(images) == 0:
            ns.abort(400, message="图像数据不能为空")

        try:
            results = detect_batch_images(images)
            return {
                'status': 'success',
                'message': f'共处理 {len(results)} 帧图像',
                'frames': results
            }
        except ValueError as ve:
            ns.abort(400, message=str(ve))
        except Exception as e:
            ns.abort(500, message=f"检测失败: {str(e)}")


# 为了在main.py中使用，我们需要导出socket处理函数
def get_pavement_socketio_handlers():
    """返回路面检测的Socket.IO事件处理器"""

    def handle_video_frame(data):
        """处理单帧视频图像"""
        from flask_socketio import emit
        from ..utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            logger.info("=== 开始处理视频帧 ===")

            # 检查数据格式
            logger.info(f"接收到的数据类型: {type(data)}")
            logger.info(f"数据键: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

            image_data = data.get('image')
            if not image_data:
                logger.error("图像数据为空")
                emit('frame_result', {'status': 'error', 'message': '图像数据为空'})
                return

            # 检查图像数据格式
            logger.info(f"图像数据长度: {len(image_data)}")
            logger.info(f"图像数据前50字符: {image_data[:50]}")

            # 检测单帧图像
            logger.info("开始调用 detect_single_image")
            result = detect_single_image(image_data)
            logger.info(f"detect_single_image 返回结果: {result}")

            # 发送检测结果
            logger.info("准备发送检测结果")
            emit('frame_result', result)
            logger.info(f"✅ 路面检测完成，检测到 {len(result.get('detections', []))} 个对象")

        except Exception as e:
            logger.error(f"❌ 处理视频帧时出错: {str(e)}", exc_info=True)
            emit('frame_result', {'status': 'error', 'message': f'处理失败: {str(e)}'})

    def handle_video_stream_end(data):
        """处理视频流结束"""
        from flask_socketio import emit
        from ..utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info('视频流处理完成')
        emit('stream_complete', {'message': '视频处理完成'})

    return {
        'video_frame': handle_video_frame,
        'video_stream_end': handle_video_stream_end
    }