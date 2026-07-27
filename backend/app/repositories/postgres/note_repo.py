"""笔记数据访问层（PostgreSQL）：使用 SQLAlchemy async 操作 notes 表"""
from datetime import datetime

from sqlalchemy import select, update, or_, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note, User
from app.core.database import get_db


# 枚举映射（与 Coze mappers 格式一致）
TYPE_REV = {1: "folder", 2: "article"}
TYPE_MAP = {"folder": 1, "article": 2}
STATUS_REV = {1: "draft", 2: "published"}
STATUS_MAP = {"draft": 1, "published": 2}


class PostgresNoteRepo:
    """笔记 Repository（PostgreSQL）：处理 notes 表的 CRUD、树查询、搜索、软删除"""

    # ── 模型 → 字典转换（与 Coze coze_to_note 返回格式一致）──
    @staticmethod
    def _to_dict(note: Note | None) -> dict | None:
        if note is None:
            return None
        return {
            "id": note.id,
            "user_id": note.user_id or 0,
            "type": TYPE_REV.get(note.type, "article"),
            "title": note.title or "",
            "slug": note.slug or "",
            "content": note.content or "",
            "parent_id": note.parent_id or 0,
            "status": STATUS_REV.get(note.status, "draft"),
            "pinned": bool(note.pinned),
            "sort_order": note.sort_order or 0,
            "word_count": note.word_count or 0,
            "is_deleted": bool(note.is_deleted),
            "deleted_at": note.deleted_at.isoformat() if note.deleted_at else None,
            "created_at": note.created_at.isoformat() if note.created_at else "",
            "updated_at": note.updated_at.isoformat() if note.updated_at else "",
        }

    # ── 基础查询 ──

    @staticmethod
    def _not_deleted_stmt():
        return select(Note).where(Note.is_deleted == 0)

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
        stmt = select(Note).where(Note.is_deleted == 0)
        if user_id is not None:
            stmt = stmt.where(Note.user_id == user_id)
        if type_:
            stmt = stmt.where(Note.type == TYPE_MAP.get(type_, 2))
        if status:
            stmt = stmt.where(Note.status == STATUS_MAP.get(status, 2))
        elif type_ != "folder":
            stmt = stmt.where(Note.status == 2)
        if parent_id is not None:
            stmt = stmt.where(Note.parent_id == parent_id)
        if keyword:
            stmt = stmt.where(Note.content.ilike(f"%{keyword}%"))

        # 排序：pinned DESC, sort_order ASC, updated_at DESC
        stmt = stmt.order_by(Note.pinned.desc(), Note.sort_order.asc(), Note.updated_at.desc())
        offset = (page_num - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        async with get_db() as session:
            result = await session.execute(stmt)
            return [self._to_dict(n) for n in result.scalars().all()]

    async def find_by_id(self, note_id: int) -> dict | None:
        """按 ID 查询单条笔记"""
        async with get_db() as session:
            result = await session.execute(
                select(Note).where(Note.id == note_id, Note.is_deleted == 0)
            )
            return self._to_dict(result.scalar_one_or_none())

    async def find_by_slug(self, slug: str) -> dict | None:
        """按 slug 查询单篇已发布文章"""
        async with get_db() as session:
            result = await session.execute(
                select(Note).where(
                    Note.slug == slug,
                    Note.type == 2,
                    Note.status == 2,
                    Note.is_deleted == 0,
                )
            )
            return self._to_dict(result.scalar_one_or_none())

    async def find_tree_records(self, user_id: int | None = None) -> list[dict]:
        """获取目录树所需记录：所有 folder + 已发布 article"""
        stmt = select(Note).where(Note.is_deleted == 0)
        if user_id is not None:
            stmt = stmt.where(Note.user_id == user_id)
        stmt = stmt.where(
            or_(
                Note.type == 1,  # folder
                and_(Note.type == 2, Note.status == 2),  # published article
            )
        )
        stmt = stmt.order_by(Note.sort_order.asc(), Note.updated_at.desc())

        async with get_db() as session:
            result = await session.execute(stmt)
            return [self._to_dict(n) for n in result.scalars().all()]

    async def find_folders(self, user_id: int | None = None) -> list[dict]:
        """查询所有目录"""
        stmt = select(Note).where(Note.type == 1, Note.is_deleted == 0)
        if user_id is not None:
            stmt = stmt.where(Note.user_id == user_id)
        stmt = stmt.order_by(Note.sort_order.asc(), Note.updated_at.desc())

        async with get_db() as session:
            result = await session.execute(stmt)
            return [self._to_dict(n) for n in result.scalars().all()]

    async def find_children(self, parent_id: int) -> list[dict]:
        """查询某个 parent 的所有子节点"""
        async with get_db() as session:
            result = await session.execute(
                select(Note).where(Note.parent_id == parent_id, Note.is_deleted == 0)
            )
            return [self._to_dict(n) for n in result.scalars().all()]

    async def is_parent_valid(self, parent_id: int | None) -> bool:
        """校验 parent_id 是否指向一个有效目录"""
        if not parent_id:
            return True
        async with get_db() as session:
            result = await session.execute(
                select(func.count(Note.id)).where(
                    Note.id == parent_id, Note.type == 1, Note.is_deleted == 0
                )
            )
            return result.scalar() > 0

    async def create(self, dto: dict) -> dict:
        """创建笔记"""
        if dto.get("parent_id"):
            if not await self.is_parent_valid(dto["parent_id"]):
                raise ValueError(f"parentId '{dto['parent_id']}' is not a valid folder")

        now = datetime.utcnow()
        note = Note(
            user_id=dto.get("user_id", 0),
            type=TYPE_MAP.get(dto.get("type", "article"), 2),
            title=dto.get("title", ""),
            slug=dto.get("slug", ""),
            content=dto.get("content", ""),
            parent_id=dto.get("parent_id", 0),
            status=STATUS_MAP.get(dto.get("status", "published"), 2),
            pinned=1 if dto.get("pinned") else 0,
            sort_order=dto.get("sort_order", 0),
            word_count=len(dto.get("content") or ""),
            is_deleted=0,
            created_at=now,
            updated_at=now,
        )
        async with get_db() as session:
            session.add(note)
            await session.flush()
            await session.refresh(note)
            return self._to_dict(note)

    async def update(self, note_id: int, dto: dict) -> dict:
        """更新笔记"""
        existing = await self.find_by_id(note_id)
        if not existing:
            raise ValueError("note not found")

        if "parent_id" in dto and dto["parent_id"] != existing.get("parent_id"):
            if not await self.is_parent_valid(dto.get("parent_id")):
                raise ValueError(f"parentId '{dto['parent_id']}' is not a valid folder")

        values = {"updated_at": datetime.utcnow()}
        if "title" in dto:
            values["title"] = dto["title"]
        if "content" in dto:
            values["content"] = dto["content"]
            values["word_count"] = len(dto["content"] or "")
        if "slug" in dto:
            values["slug"] = dto["slug"]
        if "parent_id" in dto:
            values["parent_id"] = dto["parent_id"]
        if "type" in dto:
            values["type"] = TYPE_MAP.get(dto["type"], 2)
        if "status" in dto:
            values["status"] = STATUS_MAP.get(dto["status"], 2)
        if "pinned" in dto:
            values["pinned"] = 1 if dto["pinned"] else 0
        if "sort_order" in dto:
            values["sort_order"] = dto["sort_order"]

        async with get_db() as session:
            await session.execute(
                update(Note).where(Note.id == note_id).values(**values)
            )
            await session.flush()

        return await self.find_by_id(note_id)

    async def soft_delete(self, note_id: int) -> None:
        """软删除笔记（如果是目录则递归删除子节点）"""
        existing = await self.find_by_id(note_id)
        if not existing:
            raise ValueError("note not found")

        if existing.get("type") == "folder":
            children = await self.find_children(note_id)
            for child in children:
                await self.soft_delete(child["id"])

        now = datetime.utcnow()
        async with get_db() as session:
            await session.execute(
                update(Note).where(Note.id == note_id).values(
                    is_deleted=1, deleted_at=now, updated_at=now,
                )
            )
            await session.flush()

    async def search(self, keyword: str, user_id: int | None = None) -> list[dict]:
        """全文搜索：已发布文章中标题/正文包含关键词"""
        like = f"%{keyword}%"
        stmt = select(Note).where(
            Note.is_deleted == 0,
            Note.type == 2,
            Note.status == 2,
            or_(
                Note.title.ilike(like),
                Note.content.ilike(like),
            ),
        )
        if user_id is not None:
            stmt = stmt.where(Note.user_id == user_id)
        stmt = stmt.order_by(Note.pinned.desc(), Note.updated_at.desc())

        async with get_db() as session:
            result = await session.execute(stmt)
            return [self._to_dict(n) for n in result.scalars().all()]

    async def find_all_raw(self) -> list[dict]:
        """查询全部笔记（sync 用，不加 is_deleted 过滤）"""
        async with get_db() as session:
            result = await session.execute(select(Note))
            return [self._to_dict(n) for n in result.scalars().all()]
