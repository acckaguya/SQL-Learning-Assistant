"""
一个完整的用户认证系统，包含密码哈希处理、JWT令牌生成和验证等功能
"""
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from src.backend import crud
from src.backend.database import get_db
from src.backend.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")              # 定义了OAuth2密码流程的令牌获取URL
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")   # 配置密码哈希方案，使用brypt算法


def create_access_token(data: dict):
    """
    创建访问令牌

    返回：
        str: 生成的令牌字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)    # 令牌过期时间
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)  # 使用密钥和算法编码token
    return encoded_jwt

def verify_token(token: str, db: Session):
    """
    验证令牌

    参数：
        token: 输入的令牌
        db: 数据库

    返回：
        models.User: 通过验证的用户实例
    """
    # 定义异常模板
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码令牌
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 查询具体用户，得到用户实例
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    获取当前的用户
    参数：
        token: 用户令牌
        db: 数据库
    返回：
        models.User: 用户实例
    """
    return verify_token(token, db)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    参数:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库存储的哈希密码

    返回:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码的哈希值

    返回：
        str: 密码的哈希值
    """
    return pwd_context.hash(password)