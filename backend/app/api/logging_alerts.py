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
    'timestamp': fields.String(description='日志记录时间', example='2024-07-16T12:00:00'),
    'level': fields.String(description='日志级别', example='INFO'),
    'message': fields.String(description='日志消息', example='系统启动成功'),
    'pathname': fields.String(description='代码文件路径', example='/app/main.py'),
    'lineno': fields.Integer(description='代码行号', example=42),
    'module': fields.String(description='模块名称', example='main')
})

alert_entry_model = ns.model('AlertEntry', {
    'alert_id': fields.String(readOnly=True, description='告警ID', example='A123'),
    'timestamp': fields.String(description='告警时间', example='2024-07-16T12:00:00'),
    'type': fields.String(description='告警类型', example='pavement_anomaly'),
    'description': fields.String(description='告警描述', example='检测到路面坑洞'),
    'details': fields.Raw(description='告警详情（JSON对象）', example={'frame': 1, 'confidence': 0.92}),
    'status': fields.String(description='告警状态（活跃，已处理，已忽略）', example='活跃'),
    'media_url': fields.String(description='关联媒体URL（图片或视频）', example='/static/alert_videos/road/xxx.jpg')
})

# 用于分页的通用响应模型
pagination_parser = ns.parser()
pagination_parser.add_argument('page', type=int, help='页码', default=1)
pagination_parser.add_argument('per_page', type=int, help='每页数量', default=10)


# --- 日志 API  ---
from datetime import datetime

@ns.route('/logs')
class LogList(Resource):
    @ns.doc('获取系统日志列表', parser=pagination_parser, description='获取所有系统日志，支持按级别和时间范围过滤，并进行分页')
    @ns.param('level', '按日志级别过滤 (INFO, WARNING, ERROR, DEBUG)', example='INFO')
    @ns.param('start_time', '开始时间 (ISO格式，如 2023-01-01T00:00:00 或 2023-01-01)', example='2024-07-01T00:00:00')
    @ns.param('end_time', '结束时间 (ISO格式，如 2023-01-01T23:59:59 或 2023-01-01)', example='2024-07-16T23:59:59')
    @ns.marshal_with(ns.model('LogsResponse', {
        'logs': fields.List(fields.Nested(log_entry_model)),
        'total': fields.Integer(description='总日志数', example=100),
        'page': fields.Integer(description='当前页码', example=1),
        'per_page': fields.Integer(description='每页数量', example=10)
    }))
    @ns.response(200, '获取成功')
    @ns.response(400, '参数错误')
    def get(self):
        """
        获取所有系统日志，支持按级别和时间范围过滤，并进行分页。
        参数：level, start_time, end_time, page, per_page。
        返回：日志列表及分页信息。
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


# --- 告警 API  ---
@ns.route('/alerts')
class AlertList(Resource):
    @ns.doc('获取告警事件列表', parser=pagination_parser, description='获取所有告警事件，支持按类型和状态过滤，并进行分页')
    @ns.param('type', '按告警类型过滤 (例如: unauthorized_access, pavement_anomaly)', example='pavement_anomaly')
    @ns.param('status', '按告警状态过滤 (活跃, 已处理, 已忽略)', example='活跃')
    @ns.marshal_with(ns.model('AlertsResponse', {
        'alerts': fields.List(fields.Nested(alert_entry_model)),
        'total': fields.Integer(description='总告警数', example=20),
        'page': fields.Integer(description='当前页码', example=1),
        'per_page': fields.Integer(description='每页数量', example=10)
    }))
    @ns.response(200, '获取成功')
    @ns.response(400, '参数错误')
    def get(self):
        """
        获取所有告警事件，支持按类型和状态过滤，并进行分页。
        参数：type, status, page, per_page。
        返回：告警列表及分页信息。
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
@ns.param('alert_id', '告警的唯一标识符', example='A123')
class AlertPlayback(Resource):
    @ns.doc('获取告警事件回放数据', description='根据告警ID获取告警详情及关联的媒体（图片/视频）回放数据')
    @ns.marshal_with(ns.model('AlertPlaybackResponse', {
        'alert_info': fields.Nested(alert_entry_model),
        'media_url': fields.String(description='关联的媒体文件URL，用于回放', example='/static/alert_videos/road/xxx.jpg')
    }))
    @ns.response(200, '获取成功')
    @ns.response(404, '告警未找到')
    def get(self, alert_id):
        """
        根据告警ID获取告警详情及关联的媒体（图片/视频）回放数据。
        参数：alert_id。
        返回：告警详情和媒体URL。
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

@ns.route('/logs/clear_by_time')
class ClearLogsByTime(Resource):
    @ns.doc('批量删除日志', description='按时间区间和日志级别批量删除日志（仅管理员）', security='jwt')
    @ns.response(200, '删除成功')
    @ns.response(400, '时间格式错误')
    @ns.response(403, '无权限')
    def post(self):
        """
        按时间区间和日志级别批量删除日志。
        需管理员权限。
        参数：startTime, endTime, level（JSON body）。
        返回：删除结果。
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


@ns.route('/logs/export_by_time')
class ExportLogsByTime(Resource):
    @ns.doc('导出日志为CSV', description='按时间区间和日志级别导出日志为CSV')
    @ns.param('startTime', '开始时间', example='2024-07-01')
    @ns.param('endTime', '结束时间', example='2024-07-16')
    @ns.param('level', '日志级别', example='INFO')
    @ns.response(200, '导出成功')
    @ns.response(400, '时间格式错误')
    def get(self):
        """
        按时间区间和日志级别导出日志为CSV。
        参数：startTime, endTime, level（query参数）。
        返回：CSV文件。
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


# 获取所有人脸识别告警信息（之前）
@ns.route('/face_alert_frames')
class FaceAlertFrames(Resource):    
    def get(self):
        try:
            frames = FaceAlertFrame.query.order_by(FaceAlertFrame.created_at.desc()).all()
            data = []
            for frame in frames:
                folder_path = frame.image_path  # 例如 data/alert_videos/face/video_20240716_123456
                if folder_path:
                    rel_path = folder_path.replace("\\", "/").replace("data/", "")
                    image_url = f"/static/{rel_path}/frame_00000.jpg"
                else:
                    image_url = ""
                data.append({
                    "id": frame.id,
                    "created_at": frame.created_at.isoformat() if frame.created_at else None,
                    "alert_type": frame.alert_type,
                    "confidence": frame.confidence,
                    "image_url": image_url,
                    # 你可以按需补充其他字段
                })
            return data
        except Exception as e:
            logger.error(f"获取人脸告警帧失败: {e}")
            return {'error': '获取失败'}, 500


# （可用）根据视频ID获取路面灾害告警详情
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
import shutil
@ns.route('/face_alert_frames/<int:frame_id>')
class FaceAlertFrameDelete(Resource):
    @admin_required
    def delete(self, frame_id):
        frame = FaceAlertFrame.query.get(frame_id)
        if not frame:
            return {'success': False, 'message': '告警帧不存在'}, 404

        try:
            # 判断 image_path 是文件还是文件夹
            if frame.image_path and os.path.exists(frame.image_path):
                shutil.rmtree(frame.image_path)
        except Exception as e:
            return {'success': False, 'message': f'删除文件失败: {str(e)}'}, 500

        db.session.delete(frame)
        db.session.commit()
        return {'success': True, 'message': '告警帧已删除'}

        
# (可用）路面检测视频
@ns.route('/alert_videos')
class AlertVideos(Resource):               
    def get(self):
        try:
            # 先查找 alert_frame_count=0 的记录
            zero_alert_videos = AlertVideo.query.filter_by(alert_frame_count=0).all()
            import shutil, os
            from app.extensions import db
            for video in zero_alert_videos:
                # 删除本地文件夹
                if video.save_dir and os.path.exists(video.save_dir):
                    try:
                        shutil.rmtree(video.save_dir)
                    except Exception as e:
                        logger.error(f"删除本地文件夹失败: {e}")
                # 删除数据库记录
                db.session.delete(video)
            if zero_alert_videos:
                db.session.commit()
            # 再查找剩余视频
            videos = AlertVideo.query.order_by(AlertVideo.created_at.desc()).all()
            data = [videos.to_dict() for videos in videos]
            return data
        except Exception as e:
            logger.error(f"获取路面告警视频失败: {e}")
            return {'error': '获取失败'}, 500
