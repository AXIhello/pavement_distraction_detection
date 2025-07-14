# 日志与告警接口
# backend/app/api/logging_alerts.py
from flask_restx import Namespace, Resource, fields
from flask import request
# 导入你的 LoggingService
from ..services.logging_service import LoggingService
# 导入你的日志器
from ..utils.logger import get_logger

# 导入数据库
from ..core.models import db, AlertFrame,AlertVideo
from flask import jsonify

logger = get_logger(__name__)

# 1. 定义一个命名空间 'ns'
ns = Namespace('logs_alerts', description='日志与告警管理')

# --- 定义模型 (与我之前给您的内容一致) ---
log_entry_model = ns.model('LogEntry', {
    'timestamp': fields.String(description='日志记录时间'),
    'level': fields.String(description='日志级别'),
    'message': fields.String(description='日志消息'),
    'pathname': fields.String(description='代码文件路径'),
    'lineno': fields.Integer(description='代码行号'),
    'module': fields.String(description='模块名称')
})

alert_entry_model = ns.model('AlertEntry', {
    'alert_id': fields.String(readOnly=True, description='告警ID'),
    'timestamp': fields.String(description='告警时间'),
    'type': fields.String(description='告警类型'),
    'description': fields.String(description='告警描述'),
    'details': fields.Raw(description='告警详情（JSON对象）'),
    'status': fields.String(description='告警状态（活跃，已处理，已忽略）'),
    'media_url': fields.String(description='关联媒体URL（图片或视频）')
})

# 用于分页的通用响应模型
pagination_parser = ns.parser()
pagination_parser.add_argument('page', type=int, help='页码', default=1)
pagination_parser.add_argument('per_page', type=int, help='每页数量', default=10)


# --- 日志 API (与我之前给您的内容一致) ---
@ns.route('/logs')
class LogList(Resource):
    @ns.doc('获取系统日志列表', parser=pagination_parser)
    @ns.param('level', '按日志级别过滤 (INFO, WARNING, ERROR, DEBUG)')
    @ns.param('start_time', '开始时间 (ISO格式，如 2023-01-01T00:00:00)')
    @ns.param('end_time', '结束时间 (ISO格式，如 2023-01-01T23:59:59)')
    @ns.marshal_with(ns.model('LogsResponse', {
        'logs': fields.List(fields.Nested(log_entry_model)),
        'total': fields.Integer(description='总日志数'),
        'page': fields.Integer(description='当前页码'),
        'per_page': fields.Integer(description='每页数量')
    }))
    def get(self):
        """
        获取所有系统日志，支持按级别和时间范围过滤，并进行分页。
        """
        args = pagination_parser.parse_args()
        level = request.args.get('level')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        logs_data = LoggingService.get_logs(
            level=level,
            start_time=start_time,
            end_time=end_time,
            page=args['page'],
            per_page=args['per_page']
        )
        return logs_data


# --- 告警 API (与我之前给您的内容一致) ---
@ns.route('/alerts')
class AlertList(Resource):
    @ns.doc('获取告警事件列表', parser=pagination_parser)
    @ns.param('type', '按告警类型过滤 (例如: unauthorized_access, pavement_anomaly)')
    @ns.param('status', '按告警状态过滤 (活跃, 已处理, 已忽略)')
    @ns.marshal_with(ns.model('AlertsResponse', {
        'alerts': fields.List(fields.Nested(alert_entry_model)),
        'total': fields.Integer(description='总告警数'),
        'page': fields.Integer(description='当前页码'),
        'per_page': fields.Integer(description='每页数量')
    }))
    def get(self):
        """
        获取所有告警事件，支持按类型和状态过滤，并进行分页。
        """
        args = pagination_parser.parse_args()
        alert_type = request.args.get('type')
        status = request.args.get('status')

        alerts_data = LoggingService.get_alerts(
            alert_type=alert_type,
            status=status,
            page=args['page'],
            per_page=args['per_page']
        )
        return alerts_data

@ns.route('/alerts/playback/<string:alert_id>')
@ns.param('alert_id', '告警的唯一标识符')
class AlertPlayback(Resource):
    @ns.doc('获取告警事件回放数据')
    @ns.marshal_with(ns.model('AlertPlaybackResponse', {
        'alert_info': fields.Nested(alert_entry_model),
        'media_url': fields.String(description='关联的媒体文件URL，用于回放')
    }))
    @ns.response(404, '告警未找到')
    def get(self, alert_id):
        """
        根据告警ID获取告警详情及关联的媒体（图片/视频）回放数据。
        """
        playback_data = LoggingService.get_alert_playback_data(alert_id)
        if not playback_data:
            ns.abort(404, message=f"告警 {alert_id} 未找到")
        return playback_data
    
@ns.route('/alert_frames')
class AlertFrames(Resource):
    def get(self):
        try:
            frames = AlertFrame.query.order_by(AlertFrame.created_at.desc()).all()
            data = [frame.to_dict() for frame in frames]
            return data
        except Exception as e:
            logger.error(f"获取告警帧失败: {e}")
            return {'error': '获取失败'}, 500