"""搜索服务：全文搜索已发布文章"""
from app.repositories.note_repo import NoteRepository


class SearchService:
    def __init__(self):
        self.note_repo = NoteRepository()

    async def search(
        self, keyword: str, user_id: int | None = None
    ) -> list[dict]:
        """搜索已发布文章的 title / content / ai_summary 字段"""
        if not keyword or not keyword.strip():
            return []
        records = await self.note_repo.search(keyword.strip(), user_id)
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "slug": r["slug"],
                "ai_summary": r.get("ai_summary", ""),
                "updated_at": r.get("updated_at", ""),
            }
            for r in records
        ]
