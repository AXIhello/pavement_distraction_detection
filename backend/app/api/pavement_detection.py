# backend/app/api/pavement_detection.py

from flask_restx import Namespace, Resource, fields
from ..services.pavement_service import detect_pavement_damage

# 初始化 Flask-RESTX Namespace
ns = Namespace('pavement_detection', description='路面病害检测相关操作')

# 请求参数（Base64图片）
detection_image_upload_parser = ns.parser()
detection_image_upload_parser.add_argument(
    'image', type=str, required=True, location='form', help='待检测的路面图片 (Base64编码)'
)

# 返回的单个检测项结构
detection_result_item_model = ns.model('DetectionResultItem', {
    'class': fields.String(description='病害类型，如裂缝、坑洞'),
    'confidence': fields.Float(description='检测置信度'),
    'bbox': fields.List(fields.Float, description='边界框坐标 [x1, y1, x2, y2]')
})

# 返回响应结构
detection_response_model = ns.model('DetectionResponse', {
    'status': fields.String(description='检测状态，如 success 或 failed'),
    'message': fields.String(description='检测消息'),
    'results': fields.List(fields.Nested(detection_result_item_model), description='检测到的所有病害列表')
})


@ns.route('/detect')
class DetectPavementAnomaly(Resource):
    @ns.doc('执行路面病害检测')
    @ns.expect(detection_image_upload_parser)
    @ns.marshal_with(detection_response_model)
    @ns.response(400, '无效的请求数据')
    @ns.response(500, '服务器内部错误')
    def post(self):
        """
        接收路面图片（Base64编码），进行病害检测，并返回检测结果。
        """
        args = detection_image_upload_parser.parse_args()
        image_data_base64 = args['image']

        try:
            results = detect_pavement_damage(image_data_base64)
            return {
                'status': 'success',
                'message': f'共检测到 {len(results)} 处病害',
                'results': results
            }

        except ValueError as ve:
            ns.abort(400, message=str(ve))

        except Exception as e:
            ns.abort(500, message=f"检测过程中发生错误: {str(e)}")
