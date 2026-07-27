"""笔记服务：权限校验 + CRUD 业务逻辑"""
from app.repositories import get_note_repo
from app.schemas.note import NoteCreate, NoteUpdate


class NoteService:
    def __init__(self, note_repo=None):
        self.note_repo = note_repo if note_repo is not None else get_note_repo()

    async def list_notes(
        self,
        user_id: int | None = None,
        type_: str | None = None,
        status: str | None = None,
        parent_id: int | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """查询笔记列表"""
        items = await self.note_repo.find_all(
            user_id=user_id,
            type_=type_,
            status=status,
            parent_id=parent_id,
            keyword=keyword,
            page_size=page_size,
            page_num=page,
        )
        return items, len(items)

    async def get_public_list(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """公开文章列表：仅已发布文章"""
        return await self.list_notes(
            type_="article", status="published",
            page=page, page_size=page_size,
        )

    async def get_note(self, note_id: int) -> dict:
        """获取笔记详情"""
        note = await self.note_repo.find_by_id(note_id)
        if not note:
            raise ValueError("文章不存在")
        return note

    async def get_note_by_slug(self, slug: str) -> dict:
        """通过 slug 获取公开文章"""
        note = await self.note_repo.find_by_slug(slug)
        if not note:
            raise ValueError("文章不存在")
        return note

    async def create(self, user_id: int, dto: NoteCreate) -> dict:
        """创建笔记（需用户认证）"""
        data = dto.model_dump()
        data["user_id"] = user_id

        # folder 强制 status=published
        if data.get("type") == "folder":
            data["status"] = "published"

        return await self.note_repo.create(data)

    async def update(self, note_id: int, user_id: int, dto: NoteUpdate) -> dict:
        """更新笔记（权限校验：只能更新自己的笔记）"""
        existing = await self.note_repo.find_by_id(note_id)
        if not existing:
            raise ValueError("文章不存在")
        if existing["user_id"] != user_id:
            raise PermissionError("无权编辑他人的笔记")

        # folder 强制 status=published
        data = dto.model_dump(exclude_unset=True)
        if existing.get("type") == "folder" or data.get("type") == "folder":
            data["status"] = "published"

        return await self.note_repo.update(note_id, data)

    async def delete(self, note_id: int, user_id: int) -> None:
        """软删除笔记（权限校验）"""
        existing = await self.note_repo.find_by_id(note_id)
        if not existing:
            raise ValueError("文章不存在")
        if existing["user_id"] != user_id:
            raise PermissionError("无权删除他人的笔记")
        await self.note_repo.soft_delete(note_id)
