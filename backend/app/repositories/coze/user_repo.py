"""用户数据访问层（Coze）：封装 users 表的所有 Coze API 操作"""
import asyncio
from app.core.coze_client import get_coze_client, CozeApiClient
from app.core.config import get_settings
from app.infrastructure.coze.filters import condition, and_
from app.infrastructure.coze.mappers import user_to_insert_fields, coze_to_user

settings = get_settings()

USER_FIELDS = ["id", "username", "password_hash", "email", "created_at", "is_active", "role", "pg_id"]


class CozeUserRepo:
    """用户 Repository（Coze）：处理 users 表的 CRUD"""

    def __init__(self):
        self.db_id = settings.COZE_USERS_DATABASE_ID

    async def _client(self) -> CozeApiClient:
        return await get_coze_client()

    async def find_all(self) -> list[dict]:
        """查询全部用户（sync 用，不加任何过滤）"""
        client = await self._client()
        all_records = []
        page_num = 1
        while True:
            data = await client.query(
                self.db_id,
                {
                    "select_fields": {"field_names": USER_FIELDS},
                    "page_size": 500,
                    "page_num": page_num,
                },
            )
            items = data.get("items") or []
            all_records.extend(items)
            total = int(data.get("total_count") or 0)
            if len(all_records) >= total:
                break
            page_num += 1
        return [coze_to_user(r) for r in all_records]

    async def find_by_username(self, username: str) -> dict | None:
        """按用户名查询用户（用于注册唯一性校验和登录）"""
        client = await self._client()
        from app.infrastructure.coze.filters import to_filter_dict
        data = await client.query(
            self.db_id,
            {
                "select_fields": {"field_names": USER_FIELDS},
                "page_size": 1,
                "filter": to_filter_dict(and_(condition("username", "=", username))),
            },
        )
        records = data.get("items") or []
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
        records = data.get("items") or []
        return coze_to_user(records[0]) if records else None

    async def create(
        self, username: str, password_hash: str, email: str | None = None, role: str = "user"
    ) -> dict | None:
        """创建新用户，返回创建后的用户信息

        注意：随着认证逐步迁移到 PostgreSQL，此方法仅用于 PG→Coze 同步场景。
        """
        client = await self._client()
        fields = user_to_insert_fields(username, password_hash, email, role)
        try:
            result = await client.insert(self.db_id, {"insert_rows": [fields]})
            if result.get("affected_rows", 0) == 0:
                return None
        except Exception:
            return None  # 插入失败立即返回，不重试（避免误匹配并发创建的旧用户）

        for i in range(6):
            try:
                user = await self.find_by_username(username)
                if user:
                    return user
            except Exception:
                pass
            if i < 5:
                await asyncio.sleep(1.0)
        return None

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

    # ── 同步专用方法 ──

    async def update_by_coze_id(self, coze_record_id: str, fields: dict[str, str]) -> bool:
        """按 Coze 记录 ID 更新字段（用于 sync），空字段直接跳过"""
        if not fields:
            return True
        client = await self._client()
        from app.infrastructure.coze.filters import condition, and_, to_filter_dict
        result = await client.update(self.db_id, {
            "update_fields": [{"field_name": k, "value": str(v)} for k, v in fields.items()],
            "filter": to_filter_dict(and_(condition("id", "=", coze_record_id))),
        })
        return result.get("affected_rows", 0) > 0

    async def delete_by_coze_id(self, coze_record_id: str) -> bool:
        """按 Coze 记录 ID 物理删除（用于 sync），通过 filter 匹配"""
        client = await self._client()
        from app.infrastructure.coze.filters import condition, and_, to_filter_dict
        try:
            result = await client.delete(self.db_id, {
                "filter": to_filter_dict(and_(condition("id", "=", coze_record_id))),
            })
            return result.get("affected_rows", 0) > 0
        except Exception:
            return False

    async def create_with_fields(self, fields: dict[str, str]) -> dict | None:
        """直接用字段字典创建用户（sync 用），返回创建后的用户"""
        client = await self._client()
        try:
            result = await client.insert(self.db_id, {"insert_rows": [fields]})
            if result.get("affected_rows", 0) == 0:
                return None
        except Exception:
            return None

        # 按 username 回查新建记录
        username = fields.get("username", "")
        for i in range(6):
            try:
                user = await self.find_by_username(username)
                if user:
                    return user
            except Exception:
                pass
            if i < 5:
                await asyncio.sleep(1.0)
        return None
