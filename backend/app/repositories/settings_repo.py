"""系统配置数据访问层：封装 settings 表的 Coze API 操作"""
from app.core.coze_client import get_coze_client, CozeApiClient
from app.core.config import get_settings
from app.infrastructure.coze.filters import condition, and_, to_filter_dict
from app.infrastructure.coze.mappers import setting_to_insert_fields, setting_to_update_fields, coze_to_setting

settings = get_settings()

SETTING_FIELDS = ["id", "key", "value", "updated_at"]

# 可配置的环境变量 key 列表
CONFIG_KEYS = [
    "COZE_TOKEN",
    "COZE_BASE_URL",
    "COZE_USERS_DATABASE_ID",
    "COZE_NOTES_DATABASE_ID",
    "COZE_SETTINGS_DATABASE_ID",
]


class SettingsRepository:
    """系统配置 Repository：处理 settings 表的 CRUD"""

    def __init__(self):
        self.db_id = settings.COZE_SETTINGS_DATABASE_ID

    async def _client(self) -> CozeApiClient:
        return await get_coze_client()

    async def get_all(self) -> dict[str, str]:
        """获取所有配置项，返回 {key: value} 字典"""
        client = await self._client()
        try:
            data = await client.query(
                self.db_id,
                {
                    "select_fields": {"field_names": SETTING_FIELDS},
                    "page_size": 100,
                },
            )
            records = data.get("records") or []
            result: dict[str, str] = {}
            for r in records:
                s = coze_to_setting(r)
                result[s["key"]] = s.get("value", "")
            return result
        except Exception:
            # Coze 不可达时返回空字典
            return {}

    async def get_by_key(self, key: str) -> dict | None:
        """按 key 查询单条配置"""
        client = await self._client()
        data = await client.query(
            self.db_id,
            {
                "select_fields": {"field_names": SETTING_FIELDS},
                "page_size": 1,
                "filter": to_filter_dict(and_(condition("key", "=", key))),
            },
        )
        records = data.get("records") or []
        return coze_to_setting(records[0]) if records else None

    async def upsert(self, key: str, value: str) -> bool:
        """插入或更新配置项：按 key 查找，存在则更新，不存在则插入"""
        client = await self._client()
        existing = await self.get_by_key(key)
        if existing:
            update_fields = setting_to_update_fields(key, value)
            result = await client.update(
                self.db_id,
                {
                    "record_ids": [str(existing["id"])],
                    "update_fields": update_fields,
                },
            )
            return result.get("affected_rows", 0) > 0
        else:
            fields = setting_to_insert_fields(key, value)
            result = await client.insert(self.db_id, {"insert_rows": [fields]})
            return result.get("affected_rows", 0) > 0
