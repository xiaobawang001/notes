"""FastAPI 依赖注入：从请求中提取当前用户"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_access_token
from app.core.coze_client import get_coze_client, CozeApiClient
from app.infrastructure.coze.filters import condition, and_
from app.core.config import get_settings

settings = get_settings()
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    coze: CozeApiClient = Depends(get_coze_client),
) -> dict:
    """从 JWT Token 中提取当前用户信息，返回用户字典 {id, username}

    如果 Token 无效或用户不存在，返回 None。
    使用 auto_error=False 允许公开接口不强制要求认证。
    """
    if credentials is None:
        return None

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # 查询用户是否存在且未禁用
    try:
        data = await coze.query(
            settings.COZE_USERS_DATABASE_ID,
            {
                "filter": and_(
                    condition("id", "=", user_id),
                    condition("is_active", "=", "1"),
                ),
                "page_size": 1,
            },
        )
        records = data.get("records") or []
        if not records:
            return None
        fields = records[0].get("fields") or records[0]
        return {
            "id": int(records[0].get("id") or 0),
            "username": fields.get("username", ""),
            "role": fields.get("role", "user"),
        }
    except Exception:
        return None


async def require_current_user(
    user: dict | None = Depends(get_current_user),
) -> dict:
    """强制要求登录，未认证则返回 401"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "msg": "请先登录"},
        )
    return user


async def require_admin(
    user: dict = Depends(require_current_user),
) -> dict:
    """强制要求管理员角色，非管理员返回 403"""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 403, "msg": "需要管理员权限"},
        )
    return user
