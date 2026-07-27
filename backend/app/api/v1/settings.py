"""系统配置 API 路由：管理员在线管理 Coze 环境变量"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import require_admin
from app.services.settings_service import SettingsService
from app.schemas.settings import SettingsStatus, SettingsUpdate, TestConnectionResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["settings"])


class TestConnectionRequest(BaseModel):
    """连接测试请求"""
    coze_token: str = Field(..., description="Coze Token")
    coze_base_url: str = Field(default="https://api.coze.cn", description="Coze API 地址")
    coze_users_database_id: str = Field(..., description="users 表 database ID")


def _get_service() -> SettingsService:
    return SettingsService()


@router.get("/settings", response_model=dict)
async def get_settings(user: dict = Depends(require_admin)):
    """获取当前系统配置状态（需管理员权限）"""
    svc = _get_service()
    status = await svc.get_status()
    return {
        "code": 0,
        "data": status.model_dump(),
        "msg": "success",
    }


@router.put("/settings", response_model=dict)
async def update_settings(dto: SettingsUpdate, user: dict = Depends(require_admin)):
    """更新系统配置（需管理员权限），保存后自动刷新内存缓存"""
    svc = _get_service()
    try:
        # 测试新凭据能否正常连接
        # 仅当提交了新的 token 时测试
        if dto.coze_token:
            ok = await svc.test_new_credentials(
                dto.coze_token, dto.coze_base_url, dto.coze_users_database_id
            )
            if not ok:
                raise HTTPException(
                    status_code=400,
                    detail={"code": 400, "msg": "新凭据无法连接 Coze API，请检查 Token 和 Database ID"},
                )
        await svc.update_settings(dto)
        return {"code": 0, "data": {"msg": "配置已更新"}, "msg": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": 500, "msg": f"配置更新失败: {str(e)}"},
        )


@router.post("/settings/test-connection", response_model=dict)
async def test_connection(req: TestConnectionRequest, user: dict = Depends(require_admin)):
    """测试凭据连接（需管理员权限）"""
    svc = _get_service()
    ok = await svc.test_new_credentials(
        req.coze_token, req.coze_base_url, req.coze_users_database_id
    )
    return {
        "code": 0,
        "data": {
            "success": ok,
            "message": "连接成功" if ok else "连接失败，请检查凭据",
        },
        "msg": "success",
    }
