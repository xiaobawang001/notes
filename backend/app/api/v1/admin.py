"""管理 API 路由（admin 权限）：PG/Coze 连接测试、数据同步、主后端切换

注意事项：
- switch-backend / status 端点始终通过 PG 后端认证，避免"切到 Coze 后无法切回"问题
- 其余端点使用标准依赖注入（由 URL 前缀 + 手动覆盖决定后端）
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.deps import require_admin
from app.core.backend import set_manual_backend, get_backend_status
from app.core.security import verify_access_token
from app.repositories.postgres.user_repo import PostgresUserRepo
from app.services.sync_service import SyncService

router = APIRouter(prefix="/admin", tags=["管理"])

security_scheme = HTTPBearer(auto_error=False)


class SwitchBackendRequest(BaseModel):
    backend: str  # "postgres" | "coze" | null (清除手动覆盖)


async def require_admin_pg(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> dict:
    """强制使用 PG 后端校验管理员角色（不经过 get_active_backend，不受手动覆盖影响）"""
    if credentials is None:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "请先登录"})

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "Token 无效或已过期"})

    user_id = payload.get("sub")
    username = payload.get("username")
    if not user_id and not username:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "Token 无效"})

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

    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail={"code": 401, "msg": "用户不存在或已禁用"})

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"code": 403, "msg": "需要管理员权限"})

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user.get("role", "user"),
    }


# ── PostgreSQL 连接测试 ──

@router.post("/test-pg")
async def test_pg(user: dict = Depends(require_admin)):
    """测试 PostgreSQL 连接是否可用（admin 权限）"""
    svc = SyncService()
    result = await svc.test_pg()
    return {"code": 0, "data": result, "msg": "success"}


# ── Coze 连接测试 ──

@router.post("/test-coze")
async def test_coze(user: dict = Depends(require_admin)):
    """测试 Coze API 连接是否可用（admin 权限）"""
    svc = SyncService()
    result = await svc.test_coze()
    return {"code": 0, "data": result, "msg": "success"}


# ── 数据同步（PG → Coze）──

@router.post("/sync")
async def sync_data(user: dict = Depends(require_admin)):
    """PG → Coze 增量同步（admin 权限）：全量拉取比对后按需 INSERT/UPDATE/DELETE"""
    try:
        svc = SyncService()
        result = await svc.sync()
        return {"code": 0, "data": result, "msg": "同步完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": 500, "msg": f"同步失败: {str(e)}"})


# ── 主后端切换 ──

@router.post("/switch-backend")
async def switch_backend(req: SwitchBackendRequest, user: dict = Depends(require_admin_pg)):
    """切换主后端：'postgres' | 'coze' | null（清除手动覆盖）

    ⚠️ 此端点始终通过 PG 后端认证，即使已切换到 Coze 也能切回。
    """
    if req.backend == "postgres":
        set_manual_backend("postgres")
        msg = "已切换主后端为 PostgreSQL"
    elif req.backend == "coze":
        set_manual_backend("coze")
        msg = "已切换主后端为 Coze"
    elif req.backend is None or req.backend == "null":
        set_manual_backend(None)
        msg = "已清除手动覆盖，恢复默认后端（postgres）"
    else:
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "msg": f"无效的后端类型: {req.backend}，可选: postgres / coze / null"},
        )

    return {"code": 0, "data": get_backend_status(), "msg": msg}


# ── 查看后端状态 ──

@router.get("/status")
async def backend_status(user: dict = Depends(require_admin_pg)):
    """查看当前后端状态（始终通过 PG 认证，不受手动覆盖影响）"""
    return {"code": 0, "data": get_backend_status(), "msg": "success"}
