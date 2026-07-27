"""搜索服务：全文搜索已发布文章"""
from app.repositories import get_note_repo


class SearchService:
    def __init__(self, note_repo=None):
        self.note_repo = note_repo if note_repo is not None else get_note_repo()

    async def search(
        self, keyword: str, user_id: int | None = None
    ) -> list[dict]:
        """搜索已发布文章的 title / content 字段"""
        if not keyword or not keyword.strip():
            return []
        try:
            records = await self.note_repo.search(keyword.strip(), user_id)
        except Exception:
            return []  # Coze 偶发 500，返回空结果
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "slug": r["slug"],
                "updated_at": r.get("updated_at", ""),
            }
            for r in records
        ]
