# 日志与告警接口
# backend/app/api/logging_alerts.py
from flask_restx import Namespace, Resource, fields
from flask import request, g
# 导入你的 LoggingService
from ..services.logging_service import LoggingService
# 导入你的日志器
from ..utils.logger import get_logger
from ..core.models import AlertVideo, FaceAlertVideo, db, LogEntry
import shutil, os
from functools import wraps
from flask import Response
from datetime import datetime
import csv

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user or user.get('role') != 'admin':
            return {'success': False, 'message': '无权限，管理员专用'}, 403
        return f(*args, **kwargs)
    return decorated_function

@ns.route('/alerts/<string:alert_type>/<int:alert_id>')
class AlertDelete(Resource):
    @admin_required
    def delete(self, alert_type, alert_id):
        if alert_type == 'road':
            alert = AlertVideo.query.get(alert_id)
        elif alert_type == 'face':
            alert = FaceAlertVideo.query.get(alert_id)
        else:
            return {'success': False, 'message': '未知告警类型'}, 400
        if not alert:
            return {'success': False, 'message': '告警事件不存在'}, 404
        # 删除本地缓存目录
        save_dir = alert.save_dir
        import shutil, os
        try:
            if save_dir and os.path.exists(save_dir):
                shutil.rmtree(save_dir)
        except Exception as e:
            return {'success': False, 'message': f'本地缓存删除失败: {str(e)}'}, 500
        # 删除数据库记录
        db.session.delete(alert)
        db.session.commit()
        return {'success': True, 'message': '告警事件及本地缓存已删除'}

@ns.route('/logs/clear_by_time')
class ClearLogsByTime(Resource):
    @admin_required
    def post(self):
        """
        按时间区间批量删除日志
        前端传递: {"startTime": "2024-07-01", "endTime": "2024-07-10"}
        """
        data = request.json
        # 只传日期时自动补全时间
        start_time_str = data['startTime'].strip()
        end_time_str = data['endTime'].strip()
        if len(start_time_str) == 10:
            start_time_str += ' 00:00:00'
        if len(end_time_str) == 10:
            end_time_str += ' 23:59:59'
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        logs = LogEntry.query.filter(LogEntry.timestamp >= start_time, LogEntry.timestamp <= end_time).all()
        count = len(logs)
        for log in logs:
            db.session.delete(log)
        db.session.commit()
        return {"success": True, "deleted": count}

@ns.route('/logs/export_by_time')
class ExportLogsByTime(Resource):
    def get(self):
        """
        按时间区间导出日志为CSV
        前端GET参数: ?startTime=2024-07-01&endTime=2024-07-10
        """
        start_time_str = request.args.get('startTime', '').strip()
        end_time_str = request.args.get('endTime', '').strip()
        if len(start_time_str) == 10:
            start_time_str += ' 00:00:00'
        if len(end_time_str) == 10:
            end_time_str += ' 23:59:59'
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        logs = LogEntry.query.filter(LogEntry.timestamp >= start_time, LogEntry.timestamp <= end_time).all()
        def generate():
            yield 'id,timestamp,level,message,pathname,lineno,module\n'
            for log in logs:
                yield f'{log.id},{log.timestamp},{log.level},{log.message},{log.pathname},{log.lineno},{log.module}\n'
        return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=logs.csv"})