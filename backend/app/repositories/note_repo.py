"""笔记数据访问层：封装 notes 表的所有 Coze API 操作

完全复用 TypeScript 版本 ArticleRepository 的查询逻辑，
字段名从 summary 改为 ai_summary，新增 user_id 过滤。
"""
from app.core.coze_client import get_coze_client, CozeApiClient
from app.core.config import get_settings
from app.infrastructure.coze.filters import (
    condition, and_, or_, empty_or_null,
    not_deleted_filter, to_filter_dict,
)
from app.infrastructure.coze.mappers import (
    note_to_insert_fields, note_to_update_fields,
    note_to_soft_delete_fields, coze_to_note,
    TYPE_MAP, STATUS_MAP,
)

settings = get_settings()

ALL_FIELDS = [
    "id", "user_id", "type", "title", "slug", "content", "ai_summary",
    "parent_id", "status", "pinned", "sort_order", "word_count",
    "is_deleted", "deleted_at", "created_at", "updated_at",
]

DEFAULT_SORT = [
    {"field_name": "pinned", "direction": "desc"},
    {"field_name": "sort_order", "direction": "asc"},
    {"field_name": "updated_at", "direction": "desc"},
]


class NoteRepository:
    """笔记 Repository：处理 notes 表的 CRUD、树查询、搜索、软删除"""

    def __init__(self):
        self.db_id = settings.COZE_NOTES_DATABASE_ID

    async def _client(self) -> CozeApiClient:
        return await get_coze_client()

    # ── 查询辅助 ──

    def _base_filter(self, user_id: int | None = None, **extra):
        """构建基础查询 filter：is_deleted=0 + 可选 user_id 过滤"""
        conds = [not_deleted_filter()]
        if user_id is not None:
            conds.append(condition("user_id", "=", str(user_id)))
        return and_(*conds, **extra) if extra else and_(*conds) if len(conds) > 1 else conds[0]

    async def _query(self, filter_obj, page_size=500, page_num=1, order=None):
        client = await self._client()
        body = {
            "select_fields": {"field_names": ALL_FIELDS},
            "page_size": page_size,
            "page_num": page_num,
            "filter": to_filter_dict(filter_obj),
        }
        if order:
            body["order_by"] = order
        return await client.query(self.db_id, body)

    # ── CRUD ──

    async def find_all(
        self,
        user_id: int | None = None,
        type_: str | None = None,
        status: str | None = None,
        parent_id: int | None = None,
        keyword: str | None = None,
        page_size: int = 500,
        page_num: int = 1,
    ) -> list[dict]:
        """查询笔记列表，支持组合筛选"""
        conds = [not_deleted_filter()]
        if user_id is not None:
            conds.append(condition("user_id", "=", str(user_id)))
        if type_:
            conds.append(condition("type", "=", TYPE_MAP.get(type_, "2")))
        if status:
            conds.append(condition("status", "=", STATUS_MAP.get(status, "2")))
        elif type_ != "folder":
            conds.append(condition("status", "=", "2"))
        if parent_id is not None:
            conds.append(
                condition("parent_id", "=", str(parent_id))
                if parent_id else empty_or_null("parent_id")
            )
        if keyword:
            conds.append(condition("content", "like", f"%{keyword}%"))

        filter_obj = and_(*conds)
        data = await self._query(filter_obj, page_size, page_num, DEFAULT_SORT)
        return [coze_to_note(r) for r in (data.get("records") or [])]

    async def find_by_id(self, note_id: int) -> dict | None:
        """按 ID 查询单条笔记"""
        filter_obj = and_(not_deleted_filter(), condition("id", "=", str(note_id)))
        data = await self._query(filter_obj, page_size=1)
        records = data.get("records") or []
        if records:
            return coze_to_note(records[0])
        # Fallback: 全量扫描匹配
        all_notes = await self.find_all(page_size=1000)
        return next((n for n in all_notes if n["id"] == note_id), None)

    async def find_by_slug(self, slug: str) -> dict | None:
        """按 slug 查询单篇已发布文章"""
        filter_obj = and_(
            not_deleted_filter(),
            condition("type", "=", "2"),
            condition("status", "=", "2"),
            condition("slug", "=", slug),
        )
        data = await self._query(filter_obj, page_size=1)
        records = data.get("records") or []
        return coze_to_note(records[0]) if records else None

    async def find_tree_records(self, user_id: int | None = None) -> list[dict]:
        """获取目录树所需记录：所有 folder + 已发布 article（拆分查询避 Coze 500）"""
        client = await self._client()
        base = [not_deleted_filter()]
        if user_id is not None:
            base.append(condition("user_id", "=", str(user_id)))

        folder_filter = and_(*base, condition("type", "=", "1"))
        article_filter = and_(*base, condition("type", "=", "2"), condition("status", "=", "2"))

        folder_order = [
            {"field_name": "sort_order", "direction": "asc"},
            {"field_name": "updated_at", "direction": "desc"},
        ]

        from app.infrastructure.coze.filters import to_filter_dict
        body_f = {
            "select_fields": {"field_names": ALL_FIELDS},
            "page_size": 1000,
            "filter": to_filter_dict(folder_filter),
        }
        body_a = {
            "select_fields": {"field_names": ALL_FIELDS},
            "page_size": 1000,
            "filter": to_filter_dict(article_filter),
        }

        # 串行查询（Python httpx 无内置并行）
        data_f = await client.query(self.db_id, {**body_f, "order_by": folder_order})
        data_a = await client.query(self.db_id, {**body_a, "order_by": DEFAULT_SORT})

        records_f = [coze_to_note(r) for r in (data_f.get("records") or [])]
        records_a = [coze_to_note(r) for r in (data_a.get("records") or [])]
        return records_f + records_a

    async def find_folders(self, user_id: int | None = None) -> list[dict]:
        """查询所有目录"""
        conds = [not_deleted_filter(), condition("type", "=", "1")]
        if user_id is not None:
            conds.append(condition("user_id", "=", str(user_id)))
        filter_obj = and_(*conds)
        order = [
            {"field_name": "sort_order", "direction": "asc"},
            {"field_name": "updated_at", "direction": "desc"},
        ]
        data = await self._query(filter_obj, page_size=1000, order=order)
        return [coze_to_note(r) for r in (data.get("records") or [])]

    async def find_children(self, parent_id: int) -> list[dict]:
        """查询某个 parent 的所有子节点"""
        filter_obj = and_(
            not_deleted_filter(),
            condition("parent_id", "=", str(parent_id)),
        )
        data = await self._query(filter_obj, page_size=1000)
        return [coze_to_note(r) for r in (data.get("records") or [])]

    async def is_parent_valid(self, parent_id: int | None) -> bool:
        """校验 parent_id 是否指向一个有效目录"""
        if not parent_id:
            return True
        folders = await self.find_folders()
        return any(f["id"] == parent_id for f in folders)

    async def create(self, dto: dict) -> dict:
        """创建笔记"""
        # 校验 parent_id
        if dto.get("parent_id"):
            if not await self.is_parent_valid(dto["parent_id"]):
                raise ValueError(f"parentId '{dto['parent_id']}' is not a valid folder")

        client = await self._client()
        fields = note_to_insert_fields(dto)
        result = await client.insert(self.db_id, {"insert_rows": [fields]})
        if result.get("affected_rows", 0) == 0:
            raise RuntimeError("Failed to create record")

        # 插入后回查
        conds = [
            not_deleted_filter(),
            condition("title", "=", dto.get("title", "")),
            condition("type", "=", TYPE_MAP.get(dto.get("type", "article"), "2")),
        ]
        if dto.get("parent_id"):
            conds.append(condition("parent_id", "=", str(dto["parent_id"])))
        else:
            conds.append(empty_or_null("parent_id"))
        if dto.get("user_id") is not None:
            conds.append(condition("user_id", "=", str(dto["user_id"])))

        data = await self._query(and_(*conds), page_size=1)
        records = data.get("records") or []
        if records:
            return coze_to_note(records[0])
        raise RuntimeError("Failed to retrieve created record")

    async def update(self, note_id: int, dto: dict) -> dict:
        """更新笔记"""
        existing = await self.find_by_id(note_id)
        if not existing:
            raise ValueError("note not found")

        # 校验 parent_id
        if "parent_id" in dto and dto["parent_id"] != existing.get("parent_id"):
            if not await self.is_parent_valid(dto.get("parent_id")):
                raise ValueError(f"parentId '{dto['parent_id']}' is not a valid folder")

        client = await self._client()
        update_fields = note_to_update_fields(dto)
        filter_obj = and_(not_deleted_filter(), condition("id", "=", str(note_id)))

        result = await client.update(self.db_id, {
            "update_fields": update_fields,
            "filter": to_filter_dict(filter_obj),
        })

        if result.get("affected_rows", 0) == 0:
            # Fallback: 身份过滤
            identity_conds = [
                condition("type", "=", TYPE_MAP.get(existing.get("type", "article"), "2")),
                condition("title", "=", existing.get("title", "")),
            ]
            parent_id = existing.get("parent_id")
            if existing.get("type") == "folder":
                identity_conds.append(condition("parent_id", "=", str(parent_id or "")))
            else:
                identity_conds.append(condition("slug", "=", existing.get("slug", "")))
                identity_conds.append(condition("parent_id", "=", str(parent_id or "")))
            fallback_filter = and_(*identity_conds)
            result2 = await client.update(self.db_id, {
                "update_fields": update_fields,
                "filter": to_filter_dict(fallback_filter),
            })
            if result2.get("affected_rows", 0) == 0:
                raise ValueError("note not found")

        updated = await self.find_by_id(note_id)
        if not updated:
            raise ValueError("note not found after update")
        return updated

    async def soft_delete(self, note_id: int) -> None:
        """软删除笔记（如果是目录则递归删除子节点）"""
        existing = await self.find_by_id(note_id)
        if not existing:
            raise ValueError("note not found")

        # 如果是目录，递归删除子节点
        if existing.get("type") == "folder":
            children = await self.find_children(note_id)
            for child in children:
                await self.soft_delete(child["id"])

        client = await self._client()
        fields = note_to_soft_delete_fields()
        filter_obj = and_(not_deleted_filter(), condition("id", "=", str(note_id)))

        result = await client.update(self.db_id, {
            "update_fields": fields,
            "filter": to_filter_dict(filter_obj),
        })

        if result.get("affected_rows", 0) == 0:
            # Fallback: 身份过滤
            identity_conds = [
                condition("type", "=", TYPE_MAP.get(existing.get("type", "article"), "2")),
                condition("title", "=", existing.get("title", "")),
                condition("slug", "=", existing.get("slug", "")),
                condition("parent_id", "=", str(existing.get("parent_id", 0))),
            ]
            fallback_filter = and_(*identity_conds)
            result2 = await client.update(self.db_id, {
                "update_fields": fields,
                "filter": to_filter_dict(fallback_filter),
            })
            if result2.get("affected_rows", 0) == 0:
                raise ValueError("note not found")

    async def search(self, keyword: str, user_id: int | None = None) -> list[dict]:
        """全文搜索：已发布文章中标题/正文/摘要包含关键词"""
        like = f"%{keyword}%"
        conds = [
            not_deleted_filter(),
            condition("type", "=", "2"),
            condition("status", "=", "2"),
            or_(
                condition("title", "like", like),
                condition("content", "like", like),
                condition("ai_summary", "like", like),
            ),
        ]
        if user_id is not None:
            conds.append(condition("user_id", "=", str(user_id)))

        filter_obj = and_(*conds)
        search_order = [
            {"field_name": "pinned", "direction": "desc"},
            {"field_name": "updated_at", "direction": "desc"},
        ]
        data = await self._query(filter_obj, page_size=500, order=search_order)
        return [coze_to_note(r) for r in (data.get("records") or [])]
