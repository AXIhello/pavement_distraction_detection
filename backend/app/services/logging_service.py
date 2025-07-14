# backend/app/services/logging_service.py
import datetime



mock_alerts_db = []
from ..core.models import db, LogEntry
class LoggingService:
    @staticmethod
    def add_log(level, message, pathname, lineno, module):
        """
        添加一条日志记录到 log_entries 表中。
        """
        log_entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=level,
            message=message,
            pathname=pathname,
            lineno=lineno,
            module=module
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry.to_dict()

    @staticmethod
    def get_logs(level=None, start_time=None, end_time=None, page=1, per_page=10):
        """
        从数据库查询日志记录，支持过滤和分页。
        """
        query = LogEntry.query

        if level:
            query = query.filter(LogEntry.level.ilike(level))
        if start_time:
            query = query.filter(LogEntry.timestamp >= start_time)
        if end_time:
            query = query.filter(LogEntry.timestamp <= end_time)

        total = query.count()
        logs = query.order_by(LogEntry.timestamp.desc()) \
                    .offset((page - 1) * per_page) \
                    .limit(per_page) \
                    .all()

        return {
            "logs": [log.to_dict() for log in logs],
            "total": total,
            "page": page,
            "per_page": per_page
        }
    @staticmethod
    def add_alert(alert_type, description, details=None, media_url=None):
        """
        添加一条新的告警记录。
        """
        alert_entry = {
            "alert_id": f"alert_{len(mock_alerts_db) + 1}",
            "timestamp": datetime.datetime.now().isoformat(),
            "type": alert_type,
            "description": description,
            "details": details if details else {},
            "status": "活跃", # 可以有 '活跃', '已处理', '已忽略'
            "media_url": media_url # 告警相关的图片或视频链接
        }
        mock_alerts_db.append(alert_entry)
        # 实际项目中，这里会将 alert_entry 写入数据库
        return alert_entry

    @staticmethod
    def get_alerts(alert_type=None, status=None, page=1, per_page=10):
        """
        获取告警记录，支持过滤和分页。
        """
        filtered_alerts = mock_alerts_db[:]
        if alert_type:
            filtered_alerts = [alert for alert in filtered_alerts if alert['type'] == alert_type]
        if status:
            filtered_alerts = [alert for alert in filtered_alerts if alert['status'] == status]

        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_alerts = filtered_alerts[start_index:end_index]

        return {
            "alerts": paginated_alerts,
            "total": len(filtered_alerts),
            "page": page,
            "per_page": per_page
        }

    @staticmethod
    def get_alert_playback_data(alert_id):
        """
        获取指定告警的播放数据（如图片或视频URL）。
        """
        for alert in mock_alerts_db:
            if alert['alert_id'] == alert_id:
                return {
                    "alert_info": alert,
                    "media_url": alert.get('media_url')
                }
        return None