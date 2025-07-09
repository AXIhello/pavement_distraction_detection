# backend/app/utils/logger.py
import logging
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logging(app):
    """
    配置 Flask 应用程序的日志系统。
    日志将同时输出到控制台和文件。
    """
    # 获取根日志器
    # 重要：直接配置根日志器，这样所有通过 logging.getLogger() 获取的日志器都会继承此配置
    root_logger = logging.getLogger()

    # 从 Flask 配置中获取日志级别
    log_level = app.config.get('LOG_LEVEL', logging.INFO)
    root_logger.setLevel(log_level) # 设置根日志器的最低级别

    # 确保日志目录存在
    log_dir = app.config.get('LOG_FOLDER', 'logs') # 通常在 app_config.py 中定义
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 清除所有旧的处理器，避免重复添加
    # 这一步对于根日志器是关键，因为它可能在 Flask 启动前就已经有默认处理器了
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
        # 确保 Flask 自己的 logger 处理器也被清理，防止重复输出
        # Flask 的 logger 也是 root logger 的一个子级，但有时需要单独处理
        if app.logger.handlers:
            app.logger.handlers.clear()


    # 统一的日志格式器
    formatter_console = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    formatter_file = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )


    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter_console)
    root_logger.addHandler(console_handler) # 添加到根日志器


    # 文件处理器 - 按时间轮转
    log_file_path_time = os.path.join(log_dir, 'app.log')
    time_file_handler = TimedRotatingFileHandler(
        log_file_path_time,
        when='midnight', # 每天午夜轮转
        interval=1,
        backupCount=7, # 保留最近7天的日志
        encoding='utf-8'
    )
    time_file_handler.setFormatter(formatter_file)
    root_logger.addHandler(time_file_handler) # 添加到根日志器


    app.logger.setLevel(log_level)

    root_logger.info("日志系统初始化完成")

# 可以定义一个全局函数，方便在其他模块获取日志器
def get_logger(name=None):
    """
    获取一个日志器实例。
    """
    # 获取命名的日志器，它会继承根日志器的配置
    return logging.getLogger(name if name else 'flask_app_main') # 建议给一个特定的名字，而不是 __name__
                                                                # 因为 __name__ 会因为模块不同而变化，
                                                                # 导致你可能得到很多独立的命名日志器