"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.coze_client import get_coze_client
from app.api.v1 import auth, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动/关闭 Coze 客户端"""
    # 启动：预初始化客户端
    await get_coze_client()
    yield
    # 关闭
    client = await get_coze_client()
    await client.close()


app = FastAPI(
    title="Notes App API",
    version="2.0.0",
    description="个人笔记 Web 应用 API，基于 Coze 多维表格 + FastAPI",
    lifespan=lifespan,
)

# CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理：统一返回 { code, msg } 格式
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "data": None, "msg": str(exc)},
    )


# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"code": 0, "msg": "ok"}
