"""笔记数据访问层（Coze）：封装 notes 表的所有 Coze API 操作"""
import asyncio
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
    "id", "user_id", "type", "title", "slug", "content",
    "parent_id", "status", "pinned", "sort_order", "word_count",
    "is_deleted", "deleted_at", "created_at", "updated_at", "pg_id",
]

DEFAULT_SORT = [
    {"field_name": "pinned", "direction": "desc"},
    {"field_name": "sort_order", "direction": "asc"},
    {"field_name": "updated_at", "direction": "desc"},
]


class CozeNoteRepo:
    """笔记 Repository（Coze）：处理 notes 表的 CRUD、树查询、搜索、软删除"""

    def __init__(self):
        self.db_id = settings.COZE_NOTES_DATABASE_ID

    async def _client(self) -> CozeApiClient:
        return await get_coze_client()

    # ── 查询辅助 ──
    def _base_filter(self, user_id: int | None = None, **extra):
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
        return [coze_to_note(r) for r in (data.get("items") or [])]

    async def find_by_id(self, note_id: int) -> dict | None:
        """按 ID 查询单条笔记"""
        filter_obj = and_(not_deleted_filter(), condition("id", "=", str(note_id)))
        data = await self._query(filter_obj, page_size=1)
        records = data.get("items") or []
        if records:
            return coze_to_note(records[0])
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
        records = data.get("items") or []
        return coze_to_note(records[0]) if records else None

    async def find_tree_records(self, user_id: int | None = None) -> list[dict]:
        """获取目录树所需记录：所有 folder + 已发布 article"""
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

        data_f = await client.query(self.db_id, {**body_f, "order_by": folder_order})
        data_a = await client.query(self.db_id, {**body_a, "order_by": DEFAULT_SORT})

        records_f = [coze_to_note(r) for r in (data_f.get("items") or [])]
        records_a = [coze_to_note(r) for r in (data_a.get("items") or [])]
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
        return [coze_to_note(r) for r in (data.get("items") or [])]

    async def find_children(self, parent_id: int) -> list[dict]:
        """查询某个 parent 的所有子节点"""
        filter_obj = and_(
            not_deleted_filter(),
            condition("parent_id", "=", str(parent_id)),
        )
        data = await self._query(filter_obj, page_size=1000)
        return [coze_to_note(r) for r in (data.get("items") or [])]

    async def is_parent_valid(self, parent_id: int | None) -> bool:
        """校验 parent_id 是否指向一个有效目录"""
        if not parent_id:
            return True
        folders = await self.find_folders()
        return any(f["id"] == parent_id for f in folders)

    async def create(self, dto: dict) -> dict:
        """创建笔记"""
        if dto.get("parent_id"):
            if not await self.is_parent_valid(dto["parent_id"]):
                raise ValueError(f"parentId '{dto['parent_id']}' is not a valid folder")

        client = await self._client()
        fields = note_to_insert_fields(dto)
        insert_failed = False
        try:
            result = await client.insert(self.db_id, {"insert_rows": [fields]})
            if result.get("affected_rows", 0) == 0:
                raise RuntimeError("Failed to create record")
        except Exception:
            insert_failed = True

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

        for i in range(6):
            try:
                data = await self._query(and_(*conds), page_size=1)
                records = data.get("items") or []
                if records:
                    return coze_to_note(records[0])
            except Exception:
                pass
            if i < 5:
                await asyncio.sleep(1.0)

        content = dto.get("content") or ""
        return {
            "id": 0,
            "user_id": dto.get("user_id", 0),
            "type": dto.get("type", "article"),
            "title": dto.get("title", ""),
            "slug": dto.get("slug", ""),
            "content": content,
            "parent_id": dto.get("parent_id") or 0,
            "status": dto.get("status", "published"),
            "pinned": dto.get("pinned", False),
            "sort_order": dto.get("sort_order", 0),
            "word_count": len(content),
            "is_deleted": False,
            "deleted_at": None,
            "created_at": fields.get("created_at", ""),
            "updated_at": fields.get("updated_at", ""),
        }

    async def update(self, note_id: int, dto: dict) -> dict:
        """更新笔记"""
        existing = await self.find_by_id(note_id)
        if not existing:
            raise ValueError("note not found")

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
        """全文搜索：已发布文章中标题/正文包含关键词"""
        like = f"%{keyword}%"
        conds = [
            not_deleted_filter(),
            condition("type", "=", "2"),
            condition("status", "=", "2"),
            or_(
                condition("title", "like", like),
                condition("content", "like", like),
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
        return [coze_to_note(r) for r in (data.get("items") or [])]

    # ── 同步专用方法 ──

    async def find_all_raw(self) -> list[dict]:
        """查询全部笔记（sync 用，不加 is_deleted 过滤），含 pg_id"""
        client = await self._client()
        all_records = []
        page_num = 1
        while True:
            data = await client.query(
                self.db_id,
                {
                    "select_fields": {"field_names": ALL_FIELDS},
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
        return [coze_to_note(r) for r in all_records]

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
        """直接用字段字典创建笔记（sync 用），返回创建后的记录"""
        client = await self._client()
        try:
            result = await client.insert(self.db_id, {"insert_rows": [fields]})
            if result.get("affected_rows", 0) == 0:
                return None
        except Exception:
            return None

        # 按 pg_id 回查新建记录
        pg_id = fields.get("pg_id", "")
        if pg_id:
            from app.infrastructure.coze.filters import condition, and_, to_filter_dict
            for i in range(6):
                try:
                    data = await client.query(
                        self.db_id,
                        {
                            "select_fields": {"field_names": ALL_FIELDS},
                            "page_size": 1,
                            "filter": to_filter_dict(and_(condition("pg_id", "=", str(pg_id)))),
                        },
                    )
                    records = data.get("items") or []
                    if records:
                        return coze_to_note(records[0])
                except Exception:
                    pass
                if i < 5:
                    await asyncio.sleep(1.0)
        return None
