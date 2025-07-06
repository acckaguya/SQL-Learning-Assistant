from pydantic_settings import BaseSettings
import dotenv
import os

dotenv.load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    MODEL_BASE_URL: str = os.getenv("BASE_URL")
    DATABASE_URL: str = "postgresql://postgres:123456@localhost/SQL_Assistant_v2"
    MAX_ROWS: int = 1000  # 限制查询返回行数

settings = Settings()