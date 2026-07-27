"""全局配置：从环境变量读取所有运行时参数"""
import os
from typing import Optional

from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))


class Settings:
    """应用配置，所有敏感信息从环境变量读取。"""

    _instance: Optional["Settings"] = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_env(cls) -> "Settings":
        """从 os.environ 构建配置"""
        return cls(
            # ── 默认后端（postgres 为主）──
            # 不再需要 DB_MODE 环境变量，启动时同时初始化 PG + Coze
            # 路由前缀 /postgre/v1 和 /coze/v1 始终可用
            # ── Coze API ──
            COZE_TOKEN=os.getenv("COZE_TOKEN", ""),
            COZE_BASE_URL=os.getenv("COZE_BASE_URL", "https://api.coze.cn"),
            COZE_USERS_DATABASE_ID=os.getenv("COZE_USERS_DATABASE_ID", ""),
            COZE_NOTES_DATABASE_ID=os.getenv("COZE_NOTES_DATABASE_ID", ""),
            # ── PostgreSQL ──
            PG_HOST=os.getenv("PG_HOST", "localhost"),
            PG_PORT=int(os.getenv("PG_PORT", "5432")),
            PG_DATABASE=os.getenv("PG_DATABASE", ""),
            PG_USER=os.getenv("PG_USER", ""),
            PG_PASSWORD=os.getenv("PG_PASSWORD", ""),
            PG_SSL=os.getenv("PG_SSL", "false").lower() == "true",
            # ── JWT ──
            SECRET_KEY=os.getenv("SECRET_KEY", "change-me-to-a-random-secret-key-at-least-32-chars!!"),
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=60 * 24,  # 24 小时
            # ── 调试 ──
            COZE_API_LOGGING=os.getenv("COZE_API_LOGGING", "false").lower() == "true",
        )


def get_settings() -> Settings:
    """返回当前 Settings 单例"""
    if Settings._instance is None:
        Settings._instance = Settings.from_env()
    return Settings._instance
