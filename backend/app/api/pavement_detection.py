# backend/app/api/pavement_detection.py

from flask_restx import Namespace, Resource, fields
from ..services.pavement_service import detect_batch_images

ns = Namespace('pavement_detection', description='路面病害检测相关操作')

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


@ns.route('/detect')
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
