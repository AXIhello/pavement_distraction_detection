import smtplib
import random
from email.mime.text import MIMEText
from app.app_config import Config
from flask import current_app
from datetime import datetime, timedelta

def generate_code(length=6):
    return ''.join(random.choices('0123456789', k=length))

email_code_cache = {}  # 格式: {email: {"code": "123456", "expires_at": datetime}}

def send_email(to_email, code):
    msg = MIMEText(f"您的验证码是：{code}，有效期5分钟。")
    msg['Subject'] = "登录验证码"
    msg['From'] = Config.SMTP_CONFIG['from_email']
    msg['To'] = to_email

    server = None
    try:
        server = smtplib.SMTP_SSL(Config.SMTP_CONFIG['server'], Config.SMTP_CONFIG['port'])
        server.login(Config.SMTP_CONFIG['from_email'], Config.SMTP_CONFIG['auth_code'])
        server.send_message(msg)
    except Exception as e:
        current_app.logger.error(f"邮件发送失败：{e}")
        raise
    finally:
        try:
            if server:
                server.quit()
        except Exception:
            # 忽略退出时的异常
            pass


def send_email_code(email):
    code = generate_code()
    expires_at = datetime.now() + timedelta(seconds=300)  # 5分钟后过期
    send_email(email, code)

    # 存储到内存字典
    email_code_cache[email] = {
        "code": code,
        "expires_at": expires_at
    }
    current_app.logger.info(f"验证码已发送至 {email}，内存存储成功")

def verify_email_code(email, code):
    """
    验证邮箱和验证码是否匹配
    :param email: 用户邮箱
    :param code: 用户输入的验证码
    :return: True/False
    """
    record = email_code_cache.get(email)
    if not record:
        current_app.logger.warning(f"邮箱 {email} 无验证码记录")
        return False
    
    # 检查验证码和过期时间
    is_valid = (
        record["code"] == code and 
        datetime.now() < record["expires_at"]
    )
    
    # 无论是否验证成功，移除已使用的验证码（一次性有效）
    email_code_cache.pop(email, None)
    
    return is_valid