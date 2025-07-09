# 分离数据库连接 以免循环调用
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
