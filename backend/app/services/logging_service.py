# backend/app/services/logging_service.py
import datetime

# 模拟数据库存储，实际应替换为数据库操作
mock_logs_db = []
mock_alerts_db = []

class LoggingService:  # <--- Make sure this class is defined exactly like this
    @staticmethod
    def add_log(level, message, pathname, lineno, module):
        """
        添加一条新的日志记录。
        实际项目中会将日志写入数据库。
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": level,
            "message": message,
            "pathname": pathname,
            "lineno": lineno,
            "module": module
        }
        mock_logs_db.append(log_entry)
        # 实际项目中，这里会将 log_entry 写入数据库
        return log_entry

    @staticmethod
    def get_logs(level=None, start_time=None, end_time=None, page=1, per_page=10):
        """
        从模拟数据库中获取日志记录，支持过滤和分页。
        实际项目中会从数据库查询。
        """
        filtered_logs = mock_logs_db[:]
        if level:
            filtered_logs = [log for log in filtered_logs if log['level'].lower() == level.lower()]
        if start_time:
            filtered_logs = [log for log in filtered_logs if log['timestamp'] >= start_time]
        if end_time:
            filtered_logs = [log for log in filtered_logs if log['timestamp'] <= end_time]

        # 简单的分页逻辑
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_logs = filtered_logs[start_index:end_index]

        return {
            "logs": paginated_logs,
            "total": len(filtered_logs),
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