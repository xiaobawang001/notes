"""用户数据访问层：封装 users 表的所有 Coze API 操作"""
from app.core.coze_client import get_coze_client, CozeApiClient
from app.core.config import get_settings
from app.infrastructure.coze.filters import condition, and_
from app.infrastructure.coze.mappers import user_to_insert_fields, coze_to_user

settings = get_settings()

USER_FIELDS = ["id", "username", "password_hash", "email", "created_at", "is_active", "role"]


class UserRepository:
    """用户 Repository：处理 users 表的 CRUD"""

    def __init__(self):
        self.db_id = settings.COZE_USERS_DATABASE_ID

    async def _client(self) -> CozeApiClient:
        return await get_coze_client()

    async def find_by_username(self, username: str) -> dict | None:
        """按用户名查询用户（用于注册唯一性校验和登录）"""
        client = await self._client()
        data = await client.query(
            self.db_id,
            {
                "select_fields": {"field_names": USER_FIELDS},
                "page_size": 1,
                "filter": and_(condition("username", "=", username)).__dict__
                if hasattr(condition("username", "=", username), "__dict__")
                else {},
            },
        )
        records = data.get("records") or []
        return coze_to_user(records[0]) if records else None

    async def find_by_id(self, user_id: int) -> dict | None:
        """按 ID 查询用户"""
        client = await self._client()
        from app.infrastructure.coze.filters import to_filter_dict
        data = await client.query(
            self.db_id,
            {
                "select_fields": {"field_names": USER_FIELDS},
                "page_size": 1,
                "filter": to_filter_dict(and_(condition("id", "=", str(user_id)))),
            },
        )
        records = data.get("records") or []
        return coze_to_user(records[0]) if records else None

    async def create(
        self, username: str, password_hash: str, email: str | None = None, role: str = "user"
    ) -> dict | None:
        """创建新用户，返回创建后的用户信息"""
        client = await self._client()
        fields = user_to_insert_fields(username, password_hash, email, role)
        result = await client.insert(self.db_id, {"insert_rows": [fields]})
        if result.get("affected_rows", 0) == 0:
            return None
        # 插入后回查（Coze 同步插入不返回完整记录）
        return await self.find_by_username(username)

    async def count(self) -> int:
        """统计用户总数（用于判断是否首个注册）"""
        client = await self._client()
        from app.infrastructure.coze.filters import to_filter_dict
        data = await client.query(
            self.db_id,
            {
                "select_fields": {"field_names": ["id"]},
                "page_size": 1,
            },
        )
        return int(data.get("total_count") or 0)
