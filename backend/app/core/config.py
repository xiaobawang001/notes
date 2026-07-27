"""全局配置：从环境变量读取所有运行时参数，支持运行时动态刷新"""
import os
from typing import Optional


class Settings:
    """应用配置，所有敏感信息从环境变量读取
    可通过 reload() 从 Coze settings 表动态刷新（管理员在线配置）。"""

    _instance: Optional["Settings"] = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_env(cls) -> "Settings":
        """从 os.environ 构建初始配置"""
        return cls(
            COZE_TOKEN=os.getenv("COZE_TOKEN", ""),
            COZE_BASE_URL=os.getenv("COZE_BASE_URL", "https://api.coze.cn"),
            COZE_USERS_DATABASE_ID=os.getenv("COZE_USERS_DATABASE_ID", ""),
            COZE_NOTES_DATABASE_ID=os.getenv("COZE_NOTES_DATABASE_ID", ""),
            COZE_SETTINGS_DATABASE_ID=os.getenv("COZE_SETTINGS_DATABASE_ID", ""),
            SECRET_KEY=os.getenv("SECRET_KEY", "change-me-to-a-random-secret-key-at-least-32-chars!!"),
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=60 * 24,  # 24 小时
            COZE_API_LOGGING=os.getenv("COZE_API_LOGGING", "false").lower() == "true",
        )

    def apply_overrides(self, overrides: dict[str, str]) -> None:
        """将字典中的配置项覆盖到当前实例（用于从 settings 表读取后合并）"""
        for key, value in overrides.items():
            if hasattr(self, key) and value:
                setattr(self, key, value)

    @classmethod
    def reload_from_dict(cls, overrides: dict[str, str]) -> "Settings":
        """用字典覆盖项重建单例（管理员手动刷新配置时调用）"""
        if cls._instance is None:
            cls._instance = cls.from_env()
        cls._instance.apply_overrides(overrides)
        return cls._instance


def get_settings() -> Settings:
    """返回当前 Settings 单例"""
    if Settings._instance is None:
        Settings._instance = Settings.from_env()
    return Settings._instance


def reset_settings() -> Settings:
    """重置单例（从 env 重新加载）"""
    Settings._instance = Settings.from_env()
    return Settings._instance
