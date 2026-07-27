"""系统配置服务：读取、验证、更新配置，刷新内存缓存"""
from app.repositories.settings_repo import SettingsRepository, CONFIG_KEYS
from app.core.config import get_settings, Settings
from app.core.coze_client import CozeApiError, create_test_client, reset_coze_client
from app.schemas.settings import SettingsStatus, SettingsUpdate


def _mask_token(token: str) -> str:
    """脱敏 token：仅显示前4后4字符"""
    if len(token) <= 8:
        return "*" * len(token)
    return token[:4] + "*" * (len(token) - 8) + token[-4:]


class SettingsService:
    def __init__(self):
        self.repo = SettingsRepository()

    async def get_status(self) -> SettingsStatus:
        """获取当前配置状态（含脱敏 + 连接测试结果）"""
        config = get_settings()

        # 尝试从 Coze settings 表读取实际配置
        db_settings = await self.repo.get_all()

        coze_token = db_settings.get("COZE_TOKEN") or config.COZE_TOKEN
        coze_base_url = db_settings.get("COZE_BASE_URL") or config.COZE_BASE_URL
        coze_users_db = db_settings.get("COZE_USERS_DATABASE_ID") or config.COZE_USERS_DATABASE_ID
        coze_notes_db = db_settings.get("COZE_NOTES_DATABASE_ID") or config.COZE_NOTES_DATABASE_ID
        coze_settings_db = db_settings.get("COZE_SETTINGS_DATABASE_ID") or config.COZE_SETTINGS_DATABASE_ID

        # 测试当前凭据连接
        connection_ok = await self._test_connection(coze_token, coze_base_url)

        return SettingsStatus(
            coze_token=_mask_token(coze_token),
            coze_base_url=coze_base_url,
            coze_users_database_id=coze_users_db,
            coze_notes_database_id=coze_notes_db,
            coze_settings_database_id=coze_settings_db,
            connection_ok=connection_ok,
        )

    async def _test_connection(self, token: str, base_url: str) -> bool:
        """测试凭据是否可用（用 users 表做一次轻量查询）"""
        try:
            client = create_test_client(token, base_url)
            config = get_settings()
            db_id = config.COZE_USERS_DATABASE_ID
            if not db_id:
                return False
            await client.query(db_id, {"page_size": 1})
            await client.close()
            return True
        except Exception:
            return False

    async def test_new_credentials(self, token: str, base_url: str, users_db_id: str) -> bool:
        """测试新凭据连接"""
        try:
            client = create_test_client(token, base_url)
            await client.query(users_db_id, {"page_size": 1})
            await client.close()
            return True
        except Exception:
            return False

    async def update_settings(self, dto: SettingsUpdate) -> None:
        """更新配置：先写入 Coze settings 表，再刷新内存缓存"""
        # 通过 upsert 逐个写入 settings 表
        for key, value in [
            ("COZE_TOKEN", dto.coze_token),
            ("COZE_BASE_URL", dto.coze_base_url),
            ("COZE_USERS_DATABASE_ID", dto.coze_users_database_id),
            ("COZE_NOTES_DATABASE_ID", dto.coze_notes_database_id),
            ("COZE_SETTINGS_DATABASE_ID", dto.coze_settings_database_id),
        ]:
            if value:
                await self.repo.upsert(key, value)

        # 刷新内存中的 Settings 单例
        overrides = {
            "COZE_TOKEN": dto.coze_token,
            "COZE_BASE_URL": dto.coze_base_url,
            "COZE_USERS_DATABASE_ID": dto.coze_users_database_id,
            "COZE_NOTES_DATABASE_ID": dto.coze_notes_database_id,
            "COZE_SETTINGS_DATABASE_ID": dto.coze_settings_database_id,
        }
        Settings.reload_from_dict(overrides)

        # 重置 Coze 客户端，下次请求会用新 token
        reset_coze_client()
