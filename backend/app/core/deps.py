"""FastAPI 依赖注入：从请求中提取当前用户、获取笔记仓库实例"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_access_token
from app.core.config import get_settings
from app.repositories import get_note_repo
from app.repositories.postgres.user_repo import PostgresUserRepo

settings = get_settings()
security_scheme = HTTPBearer(auto_error=False)


def get_note_repo_dep() -> "CozeNoteRepo | PostgresNoteRepo":
    """笔记仓库工厂依赖：根据 URL 前缀（或手动切换）返回对应实现"""
    return get_note_repo()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> dict | None:
    """从 JWT Token 中提取当前用户信息

    ⚠️ 始终使用 PostgreSQL 查询用户，不跟随后端切换。
    Token 由 AuthService（固定 PG）签发，用户数据仅在 PG 中存储。

    如果 Token 无效或用户不存在/已禁用，返回 None。
    使用 auto_error=False 允许公开接口不强制要求认证。
    """
    if credentials is None:
        return None

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        return None

    user_id = payload.get("sub")
    username = payload.get("username")
    if not user_id and not username:
        return None

    try:
        repo = PostgresUserRepo()
        user = None

        # 优先按 sub 查询；sub 可转整数即按 ID 查询（PG 已升级 BIGINT）
        if user_id is not None:
            try:
                uid = int(user_id)
                user = await repo.find_by_id(uid)
            except (TypeError, ValueError):
                user = None

        if user is None and username:
            user = await repo.find_by_username(username)

        if user and user.get("is_active"):
            return {
                "id": user["id"],
                "username": user["username"],
                "role": user.get("role", "user"),
            }
        return None
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
