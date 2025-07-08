import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def setup_logging(app):
    """
    配置 Flask 应用程序的日志系统。
    日志将同时输出到控制台和文件。
    """
    # 确保日志目录存在
    log_dir = app.config.get('LOG_FOLDER', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 设置根日志器的级别
    app.logger.setLevel(app.config.get('LOG_LEVEL', logging.INFO))

    # 清除旧的处理器，避免重复添加
    if not app.logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(console_handler)

        # 文件处理器 - 按大小轮转
        # log_file_path = os.path.join(log_dir, 'app.log')
        # file_handler = RotatingFileHandler(
        #     log_file_path,
        #     maxBytes=1024 * 1024 * 10, # 10 MB
        #     backupCount=5 # 保留5个备份文件
        # )
        # file_handler.setFormatter(logging.Formatter(
        #     '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        # ))
        # app.logger.addHandler(file_handler)

        # 文件处理器 - 按时间轮转 (更常用，例如每天一个文件)
        log_file_path_time = os.path.join(log_dir, 'app.log')
        time_file_handler = TimedRotatingFileHandler(
            log_file_path_time,
            when='midnight', # 每天午夜轮转
            interval=1,
            backupCount=7, # 保留最近7天的日志
            encoding='utf-8'
        )
        time_file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(time_file_handler)

    # 捕获 Flask 自己的日志（werkzeug）
    # logging.getLogger('werkzeug').addHandler(console_handler)
    # logging.getLogger('werkzeug').addHandler(time_file_handler)

    app.logger.info("日志系统初始化完成")

# 可以定义一个全局函数，方便在其他模块获取日志器
def get_logger(name=None):
    """
    获取一个日志器实例。
    """
    return logging.getLogger(name if name else __name__)