# backend/app/services/logging_service.py
import datetime


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
