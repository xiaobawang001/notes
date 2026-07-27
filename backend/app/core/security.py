"""安全工具：JWT Token 生成与验证、bcrypt 密码哈希"""
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── 密码哈希 ──
def hash_password(password: str) -> str:
    """对明文密码做 bcrypt 哈希，返回哈希后字符串"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与 bcrypt 哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token ──
def create_access_token(user_id: int, username: str, role: str = "user") -> str:
    """生成 JWT access token，载荷包含 user_id + username + role"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_access_token(token: str) -> dict | None:
    """验证 JWT token，成功返回载荷字典，失败返回 None"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
