"""全局配置：从环境变量读取所有运行时参数"""
import os
from functools import lru_cache


class Settings:
    """应用配置，所有敏感信息从环境变量读取"""

    # Coze API
    COZE_TOKEN: str = os.getenv("COZE_TOKEN", "")
    COZE_BASE_URL: str = os.getenv("COZE_BASE_URL", "https://api.coze.cn")
    COZE_USERS_DATABASE_ID: str = os.getenv("COZE_USERS_DATABASE_ID", "")
    COZE_NOTES_DATABASE_ID: str = os.getenv("COZE_NOTES_DATABASE_ID", "")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-to-a-random-secret-key-at-least-32-chars!!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时

    # 日志
    COZE_API_LOGGING: bool = os.getenv("COZE_API_LOGGING", "false").lower() == "true"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
