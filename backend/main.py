"""FastAPI 应用入口——双后端架构（PostgreSQL + Coze 始终同时运行）"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.backend import _request_backend
from app.api.v1 import auth, notes
from app.api.v1.admin import router as admin_router

settings = get_settings()

PG_PREFIX = "/postgre/v1"
COZE_PREFIX = "/coze/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：同时初始化 PostgreSQL 和 Coze 客户端"""
    # ── 启动：初始化 PG ──
    try:
        from app.core.database import init_pg_database
        await init_pg_database()
        print(f"[启动] PostgreSQL 已连接: {settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}")
    except Exception as e:
        print(f"[警告] PostgreSQL 初始化失败（服务仍可用，Coze 作为备用）: {e}")

    # ── 启动：初始化 Coze ──
    try:
        from app.core.coze_client import get_coze_client
        await get_coze_client()
        print("[启动] Coze API 客户端已就绪")
    except Exception as e:
        print(f"[警告] Coze 客户端初始化失败: {e}")

    print(f"[路由] PG: {PG_PREFIX}  |  Coze: {COZE_PREFIX}")

    yield

    # ── 关闭 ──
    try:
        from app.core.database import close_pg_database
        await close_pg_database()
        print("[关闭] PostgreSQL 连接池已释放")
    except Exception:
        pass
    try:
        from app.core.coze_client import get_coze_client
        client = await get_coze_client()
        await client.close()
        print("[关闭] Coze 客户端已关闭")
    except Exception:
        pass


app = FastAPI(
    title="Notes App API (Dual Backend)",
    version="3.0.0",
    description="PG + Coze 双后端，/postgre/v1 和 /coze/v1 始终可用",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求级别后端选择中间件：根据 URL 前缀设置 ContextVar
@app.middleware("http")
async def backend_routing_middleware(request: Request, call_next):
    if request.url.path.startswith(PG_PREFIX):
        _request_backend.set("postgres")
    elif request.url.path.startswith(COZE_PREFIX):
        _request_backend.set("coze")
    # 默认保持 postgres
    response = await call_next(request)
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "data": None, "msg": str(exc)},
    )


# 注册路由：双前缀（PG 主 + Coze 备用）
app.include_router(auth.router, prefix=PG_PREFIX)
app.include_router(notes.router, prefix=PG_PREFIX)
app.include_router(admin_router, prefix=PG_PREFIX)
app.include_router(auth.router, prefix=COZE_PREFIX)
app.include_router(notes.router, prefix=COZE_PREFIX)


# 健康检查（两个前缀都可用）
@app.get(f"{PG_PREFIX}/health")
async def health_pg():
    from app.core.backend import get_backend_status
    return {"code": 0, "msg": "ok", "backend": "postgres", **get_backend_status()}


@app.get(f"{COZE_PREFIX}/health")
async def health_coze():
    from app.core.backend import get_backend_status
    return {"code": 0, "msg": "ok", "backend": "coze", **get_backend_status()}
