"""
数据库和会话管理核心模块，功能为创建数据库引擎、会话工厂和提供数据库会话的依赖项
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import settings

# 创建数据库引擎
engine = create_engine(settings.DATABASE_URL)

# 创建会话工厂，禁止自动提交，禁止自动刷新，绑定到上文创建的数据库引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建ORM基类，用于models中定义数据库表结构中对应的python类
Base = declarative_base()

# 数据库会话依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db        # 将会话提供给调用的函数使用
    finally:
        db.close()      # 使用后关闭