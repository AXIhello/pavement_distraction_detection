# 日志与告警接口
# backend/app/api/logging_alerts.py
from flask_restx import Namespace, Resource, fields
from flask import request, g
# 导入你的 LoggingService
from ..services.logging_service import LoggingService
# 导入你的日志器
from ..utils.logger import get_logger
from ..core.models import AlertVideo,db, AlertFrame, FaceAlertFrame,LogEntry
from functools import wraps
from flask import Response
from datetime import datetime

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


# --- 日志 API  ---
from datetime import datetime

@ns.route('/logs')
class LogList(Resource):
    @ns.doc('获取系统日志列表', parser=pagination_parser)
    @ns.param('level', '按日志级别过滤 (INFO, WARNING, ERROR, DEBUG)')
    @ns.param('start_time', '开始时间 (ISO格式，如 2023-01-01T00:00:00 或 2023-01-01)')
    @ns.param('end_time', '结束时间 (ISO格式，如 2023-01-01T23:59:59 或 2023-01-01)')
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
        start_time = request.args.get('start_time', '').strip()
        end_time = request.args.get('end_time', '').strip()

        # 自动补全时间字符串，如果只有日期部分则补全时分秒
        if start_time and len(start_time) == 10:
            start_time += 'T00:00:00'  # 补成当天开始时间，符合 ISO8601 格式
        if end_time and len(end_time) == 10:
            end_time += 'T23:59:59'  # 补成当天结束时间，符合 ISO8601 格式

        logs_data = LoggingService.get_logs(
            level=level,
            start_time=start_time if start_time else None,
            end_time=end_time if end_time else None,
            page=args['page'],
            per_page=args['per_page']
        )
        return logs_data


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'user', None)
        if not user or user.get('role') != 'admin':
            return {'success': False, 'message': '无权限，管理员专用'}, 403
        return f(*args, **kwargs)
    return decorated_function

# 删除告警信息用
@ns.route('/alerts/<string:alert_type>/<int:alert_id>')
class AlertDelete(Resource):
    @admin_required
    def delete(self, alert_type, alert_id):
        if alert_type == 'road':
            alert = AlertVideo.query.get(alert_id)
        elif alert_type == 'face':
            alert = FaceAlertFrame.query.get(alert_id)
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

# 清除日志
@ns.route('/logs/clear_by_time')
class ClearLogsByTime(Resource):
    @admin_required
    def post(self):
        """
        按时间区间和日志级别批量删除日志
        前端传递: {"startTime": "2024-07-01", "endTime": "2024-07-10", "level": "ERROR"}
        level 可选
        """
        from datetime import datetime

        data = request.json
        start_time_str = data.get('startTime', '').strip()
        end_time_str = data.get('endTime', '').strip()
        level = data.get('level', '').strip().upper()

        # 初始化，防止未定义错误
        start_time = None
        end_time = None

        # 自动补全时间
        if start_time_str and len(start_time_str) == 10:
            start_time_str += ' 00:00:00'
        if end_time_str and len(end_time_str) == 10:
            end_time_str += ' 23:59:59'

        # 转换时间字符串为 datetime 对象，容错处理
        try:
            if start_time_str:
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            if end_time_str:
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {"message": "时间格式错误，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS"}, 400

        query = LogEntry.query
        if start_time:
            query = query.filter(LogEntry.timestamp >= start_time)
        if end_time:
            query = query.filter(LogEntry.timestamp <= end_time)
        if level:
            query = query.filter(LogEntry.level == level)

        logs = query.all()
        count = len(logs)

        for log in logs:
            db.session.delete(log)
        db.session.commit()

        return {"success": True, "deleted": count}

# 导出日志
@ns.route('/logs/export_by_time')
class ExportLogsByTime(Resource):
    def get(self):
        """
        按时间区间和日志级别导出日志为CSV
        GET参数: ?startTime=2024-07-01&endTime=2024-07-10&level=INFO
        """
        import csv, io
        from flask import Response, request
        from datetime import datetime

        start_time_str = request.args.get('startTime', '').strip()
        end_time_str = request.args.get('endTime', '').strip()
        level = request.args.get('level', '').strip().upper()

        query = LogEntry.query

        # 初始化，防止变量未定义
        start_time = None
        end_time = None

        # 时间处理
        if start_time_str and len(start_time_str) == 10:
            start_time_str += ' 00:00:00'
        if end_time_str and len(end_time_str) == 10:
            end_time_str += ' 23:59:59'

        try:
            if start_time_str:
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                query = query.filter(LogEntry.timestamp >= start_time)
            if end_time_str:
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                query = query.filter(LogEntry.timestamp <= end_time)
        except ValueError:
            return {"message": "时间格式错误，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS"}, 400

        # 级别处理
        if level:
            query = query.filter(LogEntry.level == level)

        logs = query.all()

        # 提前脱离 session：序列化为 dict，避免 lazy loading 错误
        logs_data = [{
            'id': log.id,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'level': log.level,
            'message': log.message,
            'pathname': log.pathname,
            'lineno': log.lineno,
            'module': log.module
        } for log in logs]

        # 生成 CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'timestamp', 'level', 'message', 'pathname', 'lineno', 'module'])
        writer.writeheader()
        for row in logs_data:
            writer.writerow(row)

        # 加 BOM 前缀防止中文乱码
        bom = '\ufeff'
        csv_data = bom + output.getvalue()
        output.close()

        filename = f"logs_{start_time_str[:10] if start_time else 'ALL'}_{end_time_str[:10] if end_time else 'ALL'}.csv"
        return Response(csv_data, mimetype='text/csv; charset=utf-8',
                        headers={"Content-Disposition": f"attachment; filename={filename}"})


# 获取所有人脸识别告警信息
@ns.route('/face_alert_frames')
class FaceAlertFrames(Resource):    
    def get(self):
        try:
            frames = FaceAlertFrame.query.order_by(FaceAlertFrame.created_at.desc()).all()
            data = [frame.to_dict() for frame in frames]
            return data
        except Exception as e:
            logger.error(f"获取人脸告警帧失败: {e}")
            return {'error': '获取失败'}, 500


# 根据视频ID获取路面灾害告警详情
@ns.route('/alert_video_detail/<int:video_id>',methods=['GET'])
class AlertVideoDetail(Resource):               
    def get(self, video_id):
        try:
            # 查询视频信息
            video = AlertVideo.query.get(video_id)
            if not video:
                return {'error': '未找到对应视频'}, 404

            # 查询该视频下的所有帧（如果有）
            frames = AlertFrame.query.filter_by(video_id=video_id).order_by(AlertFrame.created_at.asc()).all()

            # 构造响应数据
            data = {
                'id': frames[0].video_id,  # 用第一条的 video_id
                'created_at': frames[0].created_at.isoformat() if frames[0].created_at else None,
                'disease_type': frames[0].disease_type,  # 这里可以按需求改成列表里所有类型或第一个
                'description': f'共检测到{len(frames)}帧告警',
                'frames': []
            }

            for f in frames:
                data['frames'].append({
                    'frame_index': f.frame_index,
                    'disease_type': f.disease_type,
                    'confidence': f.confidence,
                    'image_url': f.image_path,
                    'created_at': f.created_at.isoformat() if f.created_at else None
                })
            return data
        except Exception as e:
            logger.error(f"获取人脸告警视频详情失败: {e}")
            return {'error': '获取失败'}, 500


# 删除人脸识别告警帧
import os
@ns.route('/face_alert_frames/<int:frame_id>')
class FaceAlertFrameDelete(Resource):
    @admin_required
    def delete(self, frame_id):
        frame = FaceAlertFrame.query.get(frame_id)
        if not frame:
            return {'success': False, 'message': '告警帧不存在'}, 404

        try:
            # 如果有对应的本地缓存文件需要删除，也可在这里做
            if frame.image_path and os.path.exists(frame.image_path):
                os.remove(frame.image_path)
        except Exception as e:
            return {'success': False, 'message': f'删除文件失败: {str(e)}'}, 500

        db.session.delete(frame)
        db.session.commit()
        return {'success': True, 'message': '告警帧已删除'}

        
# 获取路面检测视频
@ns.route('/alert_videos')
class AlertVideos(Resource):               
    def get(self):
        try:
            videos = AlertVideo.query.order_by(AlertVideo.created_at.desc()).all()
            data = [videos.to_dict() for videos in videos]
            return data
        except Exception as e:
            logger.error(f"获取路面告警视频失败: {e}")
            return {'error': '获取失败'}, 500
