"""Repository 层：根据请求上下文（URL 前缀）自动选择 Coze 或 PostgreSQL 实现

所有外部代码通过工厂函数获取仓库实例：
    from app.repositories import get_user_repo, get_note_repo
    user_repo = get_user_repo()
    note_repo = get_note_repo()
"""
from app.repositories.postgres.user_repo import PostgresUserRepo
from app.repositories.postgres.note_repo import PostgresNoteRepo
from app.repositories.coze.user_repo import CozeUserRepo
from app.repositories.coze.note_repo import CozeNoteRepo
from app.core.backend import get_active_backend


def get_user_repo():
    """返回当前请求对应的 UserRepository 实例（工厂函数）"""
    if get_active_backend() == "postgres":
        return PostgresUserRepo()
    return CozeUserRepo()


def get_note_repo():
    """返回当前请求对应的 NoteRepository 实例（工厂函数）"""
    if get_active_backend() == "postgres":
        return PostgresNoteRepo()
    return CozeNoteRepo()


# 向后兼容别名：Service 层通过工厂函数获取实例
# 外部代码应使用 get_user_repo() / get_note_repo()
__all__ = ["get_user_repo", "get_note_repo"]
