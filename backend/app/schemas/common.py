"""Pydantic 通用模型：统一响应格式、分页"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    """统一 API 响应格式：{ code: 0, data: {...}, msg: \"success\" }"""
    code: int = Field(default=0, description="状态码，0 表示成功")
    data: Any = Field(default=None, description="响应数据")
    msg: str = Field(default="success", description="提示信息")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int = Field(description="错误状态码（非0）")
    msg: str = Field(description="错误描述信息")


class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int = Field(description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    has_more: bool = Field(default=False, description="是否有更多")


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
