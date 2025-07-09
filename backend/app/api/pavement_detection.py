# backend/app/api/pavement_detection.py

from flask_restx import Namespace, Resource, fields
from flask_socketio import emit # 统一导入 emit
from ..services.pavement_service import detect_single_image, detect_batch_images # 统一导入 detect_batch_images
from ..utils.logger import get_logger # 统一导入 logger

# 获取日志器实例
logger = get_logger(__name__)

ns = Namespace('pavement_detection', description='路面病害检测相关操作')

# 定义用于批量检测的请求解析器
parser = ns.parser()
parser.add_argument(
    'images', type=str, action='split', required=True, location='form',
    help='一组Base64编码的图片字符串，用英文逗号分隔'
)

# 定义检测结果项的模型
detection_result_item_model = ns.model('DetectionResultItem', {
    'class': fields.String(description='检测到的病害类别'),
    'confidence': fields.Float(description='检测置信度'),
    'bbox': fields.List(fields.Float, description='边界框坐标 [xmin, ymin, xmax, ymax]'),
    'error': fields.String(required=False, description='处理错误信息（如果存在）')
})

# 定义单帧检测结果的模型
frame_result_model = ns.model('FrameResult', {
    'frame_index': fields.Integer(description='帧索引'),
    'detections': fields.List(fields.Nested(detection_result_item_model), description='该帧中检测到的所有对象'),
    'image_base64': fields.String(required=False, description='标注后的图像Base64编码（仅在成功时返回）'),
    'status': fields.String(description='处理状态，"success" 或 "error"'),
    'message': fields.String(required=False, description='处理消息或错误信息')
})

# 定义批量检测响应的模型
detection_response_model = ns.model('DetectionResponse', {
    'status': fields.String(description='整体处理状态'),
    'message': fields.String(description='整体处理消息'),
    'frames': fields.List(fields.Nested(frame_result_model), description='每帧的检测结果列表')
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
        对一组路面图像（Base64编码）执行病害检测。
        此API用于批量处理图像，返回每帧的检测结果。
        """
        args = parser.parse_args()
        images = args['images']

        if not isinstance(images, list) or len(images) == 0:
            logger.warning("收到空的或无效的图像数据进行批量检测")
            ns.abort(400, message="图像数据不能为空")

        try:
            # 调用服务层进行批量检测
            results = detect_batch_images(images)
            logger.info(f"成功处理 {len(results)} 帧图像的批量检测请求。")
            return {
                'status': 'success',
                'message': f'共处理 {len(results)} 帧图像',
                'frames': results
            }
        except ValueError as ve:
            logger.error(f"批量检测请求参数错误: {str(ve)}")
            ns.abort(400, message=str(ve))
        except Exception as e:
            logger.exception(f"批量检测服务器内部错误: {str(e)}") # 使用logger.exception 打印完整堆栈
            ns.abort(500, message=f"检测失败: {str(e)}")


def get_pavement_socketio_handlers():
    """
    返回路面检测的Socket.IO事件处理器。
    这些处理器用于实时视频流的单帧处理。
    """

    def handle_video_frame(data: dict):
        """
        处理从客户端接收到的单帧视频图像数据。
        对图像进行病害检测，并将结果通过Socket.IO发送回客户端。
        """
        logger.info("开始处理视频帧...")

        image_data = data.get('image')
        if not image_data:
            logger.error("视频帧图像数据为空。")
            emit('frame_result', {'status': 'error', 'message': '图像数据为空', 'detections': [], 'annotated_image': None})
            return

        try:
            # 调用服务层进行单帧图像检测
            result = detect_single_image(image_data)
            # 根据detect_single_image的返回结果发送给客户端
            emit('frame_result', result)
            if result.get('status') == 'success':
                logger.info(f"视频帧检测完成，检测到 {len(result.get('detections', []))} 个对象。")
            else:
                logger.warning(f"视频帧检测失败: {result.get('message')}")

        except Exception as e:
            logger.exception(f"处理视频帧时发生未预期错误: {str(e)}") # 使用logger.exception 打印完整堆栈
            emit('frame_result', {'status': 'error', 'message': f'处理失败: {str(e)}', 'detections': [], 'annotated_image': None})

    def handle_video_stream_end(data: dict):
        """
        处理视频流结束信号。
        通知客户端视频处理已完成。
        """
        logger.info('收到视频流结束信号，视频流处理完成。')
        emit('stream_complete', {'message': '视频处理完成'})

    return {
        'video_frame': handle_video_frame,
        'video_stream_end': handle_video_stream_end
    }
