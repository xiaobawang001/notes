"""认证相关 Pydantic Schema"""
import re

from pydantic import BaseModel, Field, field_validator

# 邮箱格式正则（基础校验）
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: str | None = Field(default=None, max_length=200, description="邮箱（可选）")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and v.strip() and not EMAIL_PATTERN.match(v):
            raise ValueError("邮箱格式不正确")
        return v.strip() if v else None


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
