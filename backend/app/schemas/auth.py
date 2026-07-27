"""认证相关 Pydantic Schema"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: str | None = Field(default=None, max_length=200, description="邮箱（可选）")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer")
    user_id: int = Field(description="用户 ID")
    username: str = Field(description="用户名")
    role: str = Field(description="角色：user / admin")


class RefreshRequest(BaseModel):
    """刷新 Token 请求"""
    token: str = Field(..., description="当前 token")
