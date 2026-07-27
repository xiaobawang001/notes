"""PostgreSQL 异步数据库连接（使用 SQLAlchemy 2.0 async + asyncpg）

仅在 DB_MODE=postgres 时初始化，Coze 模式下不会加载。
"""
from contextlib import asynccontextmanager

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import get_settings

settings = get_settings()

# 全局引擎和会话工厂（延迟初始化）
engine = None
AsyncSessionLocal = None


async def init_pg_database():
    """初始化 PostgreSQL 异步引擎并自动创建表"""
    global engine, AsyncSessionLocal
    url_object = URL.create(
        "postgresql+asyncpg",
        username=settings.PG_USER,
        password=settings.PG_PASSWORD,
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        database=settings.PG_DATABASE,
        query={"ssl": "require"} if settings.PG_SSL else {},
    )
    engine = create_async_engine(url_object, echo=False, pool_size=10, max_overflow=20)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 自动建表（checkfirst=True：表已存在则跳过，避免权限报错）
    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)


async def close_pg_database():
    """关闭 PostgreSQL 连接池"""
    global engine
    if engine:
        await engine.dispose()
        engine = None


@asynccontextmanager
async def get_db():
    """获取数据库会话的上下文管理器（用于仓库内部）"""
    if AsyncSessionLocal is None:
        raise RuntimeError("PostgreSQL 未初始化，请确认 DB_MODE=postgres 且已调用 init_pg_database()")
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
