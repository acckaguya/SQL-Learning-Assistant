"""
一些基本设置
"""
from pydantic_settings import BaseSettings
import dotenv
import os

dotenv.load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = "secret"                                                          # 密钥
    ALGORITHM: str = "HS256"                                                            # 编码算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30                                               # 令牌最大时间
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")                                   # LLM-API-KEY
    MODEL_BASE_URL: str = os.getenv("BASE_URL")                                         # LLM地址
    DATABASE_URL: str = "postgresql://postgres:123456@localhost/SQL_Assistant_v2"       # 数据库连接
    MAX_ROWS: int = 1000  # 限制查询返回行数

settings = Settings()