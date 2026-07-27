"""后端选择模块：通过 ContextVar + 中间件实现请求级后端路由，支持运行时切换"""
from contextvars import ContextVar
from typing import Literal

BackendType = Literal["postgres", "coze"]

# 请求级别后端选择（由中间件根据 URL 前缀设置）
_request_backend: ContextVar[BackendType] = ContextVar("_request_backend", default="postgres")

# 运行时手动切换标志（admin 接口设置，重启后恢复默认）
_manual_override: BackendType | None = None


def set_manual_backend(backend: BackendType | None) -> None:
    """管理接口调用：手动切换主后端（防 PG 宕机）"""
    global _manual_override
    _manual_override = backend


def get_active_backend() -> BackendType:
    """获取当前请求应使用的后端：
    1. 如果有手动覆盖，返回手动指定
    2. 否则返回 ContextVar（由中间件根据 URL 前缀设置）
    如果没有请求上下文（如 lifespan），默认返回 postgres
    """
    if _manual_override is not None:
        return _manual_override
    try:
        return _request_backend.get()
    except LookupError:
        return "postgres"


def get_backend_status() -> dict:
    """获取当前后端状态（供 admin 接口查询）"""
    return {
        "active_backend": get_active_backend(),
        "manual_override": _manual_override is not None,
        "manual_backend": _manual_override,
    }
