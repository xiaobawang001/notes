"""认证相关 API 路由"""
from fastapi import APIRouter, HTTPException

from app.schemas.auth import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse
from app.schemas.common import StandardResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=StandardResponse)
async def register(req: RegisterRequest):
    """用户注册"""
    try:
        svc = AuthService()
        token = await svc.register(req)
        return StandardResponse(data=token.model_dump(), msg="注册成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": 400, "msg": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": 500, "msg": str(e)})


@router.post("/login", response_model=StandardResponse)
async def login(req: LoginRequest):
    """用户登录"""
    try:
        svc = AuthService()
        token = await svc.login(req)
        return StandardResponse(data=token.model_dump(), msg="登录成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": 400, "msg": str(e)})


@router.post("/refresh", response_model=StandardResponse)
async def refresh(req: RefreshRequest):
    """刷新 Token"""
    try:
        svc = AuthService()
        token = await svc.refresh_token(req.token)
        return StandardResponse(data=token.model_dump(), msg="刷新成功")
    except ValueError as e:
        raise HTTPException(status_code=401, detail={"code": 401, "msg": str(e)})
