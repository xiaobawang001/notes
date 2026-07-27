"""Coze 字段与领域对象之间的双向映射

Coze API 所有字段值以字符串传输（即使字段类型是 Integer/Time），
本模块负责领域对象 ↔ Coze 记录之间的转换。
"""
from datetime import datetime, timezone
from typing import Optional


# ── 枚举映射 ──
TYPE_MAP = {"folder": "1", "article": "2"}
TYPE_MAP_REV = {"1": "folder", "2": "article"}
STATUS_MAP = {"draft": "1", "published": "2"}
STATUS_MAP_REV = {"1": "draft", "2": "published"}
PINNED_MAP = {False: "0", True: "1"}
PINNED_MAP_REV = {"0": False, "1": True}
DELETED_MAP = {False: "0", True: "1"}
DELETED_MAP_REV = {"0": False, "1": True}
ROLE_MAP = {"user": "user", "admin": "admin"}
ACTIVE_MAP = {False: "0", True: "1"}
ACTIVE_MAP_REV = {"0": False, "1": True}


def now_iso() -> str:
    """当前时间 ISO 8601 字符串"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ── Users 映射 ──

def user_to_insert_fields(
    username: str,
    password_hash: str,
    email: Optional[str] = None,
    role: str = "user",
) -> dict[str, str]:
    """用户注册：构建插入字段"""
    fields: dict[str, str] = {
        "username": username,
        "password_hash": password_hash,
        "created_at": now_iso(),
        "is_active": "1",
        "role": role,
    }
    if email:
        fields["email"] = email
    return fields


def coze_to_user(record: dict) -> dict:
    """Coze 记录 → 用户字典"""
    fields = record.get("fields") or record
    return {
        "id": int(record.get("id") or 0),
        "username": fields.get("username", ""),
        "password_hash": fields.get("password_hash", ""),
        "email": fields.get("email", ""),
        "created_at": fields.get("created_at", ""),
        "is_active": ACTIVE_MAP_REV.get(fields.get("is_active", "1"), True),
        "role": fields.get("role", "user"),
        "pg_id": fields.get("pg_id", ""),
    }


# ── Notes 映射 ──

def note_to_insert_fields(dto: dict) -> dict[str, str]:
    """创建笔记：构建插入字段"""
    content = dto.get("content") or ""
    fields: dict[str, str] = {
        "user_id": str(dto.get("user_id", 0)),
        "type": TYPE_MAP.get(dto.get("type", "article"), "2"),
        "title": dto.get("title", ""),
        "parent_id": str(dto.get("parent_id") or 0),
        "status": STATUS_MAP.get(dto.get("status", "published"), "2"),
        "pinned": PINNED_MAP.get(dto.get("pinned", False), "0"),
        "sort_order": str(dto.get("sort_order") or 0),
        "word_count": str(len(content)),
        "is_deleted": "0",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    if dto.get("slug"):
        fields["slug"] = dto["slug"]
    if content:
        fields["content"] = content
    return fields


def note_to_update_fields(dto: dict) -> list[dict]:
    """更新笔记：构建更新字段列表（仅包含变更字段 + 自动更新时间戳）"""
    update_fields: list[dict] = []

    def _add(name: str, value: str):
        update_fields.append({"field_name": name, "value": str(value)})

    if "title" in dto:
        _add("title", dto["title"])
    if "content" in dto:
        content = dto["content"] or ""
        _add("content", content)
        _add("word_count", len(content))
    if "slug" in dto:
        _add("slug", dto["slug"] or "")
    if "parent_id" in dto:
        _add("parent_id", dto["parent_id"] or 0)
    if "type" in dto:
        _add("type", TYPE_MAP.get(dto["type"], "2"))
    if "status" in dto:
        _add("status", STATUS_MAP.get(dto["status"], "2"))
    if "pinned" in dto:
        _add("pinned", PINNED_MAP.get(dto["pinned"], "0"))
    if "sort_order" in dto:
        _add("sort_order", dto["sort_order"])

    # 始终更新时间戳
    _add("updated_at", now_iso())
    return update_fields


def note_to_soft_delete_fields() -> list[dict]:
    """软删除字段"""
    now = now_iso()
    return [
        {"field_name": "is_deleted", "value": "1"},
        {"field_name": "deleted_at", "value": now},
        {"field_name": "updated_at", "value": now},
    ]


def coze_to_note(record: dict) -> dict:
    """Coze 记录 → 笔记字典"""
    fields = record.get("fields") or record
    return {
        "id": int(record.get("id") or 0),
        "user_id": int(fields.get("user_id") or 0),
        "type": TYPE_MAP_REV.get(fields.get("type", ""), "article"),
        "title": fields.get("title", ""),
        "slug": fields.get("slug", ""),
        "content": fields.get("content", ""),
        "parent_id": int(fields.get("parent_id") or 0),
        "status": STATUS_MAP_REV.get(fields.get("status", ""), "draft"),
        "pinned": PINNED_MAP_REV.get(fields.get("pinned", "0"), False),
        "sort_order": int(fields.get("sort_order") or 0),
        "word_count": int(fields.get("word_count") or 0),
        "is_deleted": DELETED_MAP_REV.get(fields.get("is_deleted", "0"), False),
        "deleted_at": fields.get("deleted_at"),
        "created_at": fields.get("created_at", ""),
        "updated_at": fields.get("updated_at", ""),
        "pg_id": fields.get("pg_id", ""),
    }

