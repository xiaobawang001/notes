"""数据同步服务：PG → Coze 全量比对 + 增量同步

策略：
1. 拉取 PG + Coze 全量数据到服务端内存
2. 按 pg_id（users 按 username）匹配比对业务字段
3. 按需 UPDATE / INSERT / DELETE（排除 Coze 平台字段：id, sys_platform, uuid, bstudio_create_time）
4. Coze 多余数据物理删除，保持与 PG 一致
"""
from datetime import datetime

from app.repositories.postgres.user_repo import PostgresUserRepo
from app.repositories.postgres.note_repo import PostgresNoteRepo
from app.repositories.coze.user_repo import CozeUserRepo
from app.repositories.coze.note_repo import CozeNoteRepo

# Coze 平台自有字段（不参与比对、不参与写入）
COZE_PLATFORM_FIELDS = {"id", "sys_platform", "uuid", "bstudio_create_time"}

# users 业务字段（参与比对/同步，不含 created_at——不可变审计字段）
USER_BUSINESS_FIELDS = ["username", "password_hash", "email", "is_active", "role"]

# notes 业务字段（参与比对/同步，不含 pg_id，pg_id 只用于匹配）
NOTE_BUSINESS_FIELDS = [
    "user_id", "type", "title", "slug", "content",
    "parent_id", "status", "pinned", "sort_order", "word_count",
    "is_deleted", "deleted_at", "created_at", "updated_at",
]


class SyncService:
    """PG → Coze 全量增量同步引擎"""

    def __init__(self):
        self.pg_users = PostgresUserRepo()
        self.pg_notes = PostgresNoteRepo()
        self.coze_users = CozeUserRepo()
        self.coze_notes = CozeNoteRepo()

        # 映射表：{pg_user_id: coze_record_id}
        self.user_id_map: dict[int, str] = {}

    async def test_pg(self) -> dict:
        """测试 PostgreSQL 连接是否可用"""
        try:
            count = await self.pg_users.count()
            return {"ok": True, "message": f"PostgreSQL 连接正常，用户数: {count}"}
        except Exception as e:
            return {"ok": False, "message": f"PostgreSQL 连接失败: {str(e)}"}

    async def test_coze(self) -> dict:
        """测试 Coze API 连接是否可用"""
        try:
            count = await self.coze_users.count()
            return {"ok": True, "message": f"Coze API 连接正常，用户数: {count}"}
        except Exception as e:
            return {"ok": False, "message": f"Coze API 连接失败: {str(e)}"}

    # ── 字段比对 ──

    # 时间字段名集合（需规范化格式后比较）
    TIME_FIELDS = {"created_at", "updated_at", "deleted_at"}

    @staticmethod
    def _normalize(val: str, field_name: str) -> str:
        """规范化字段值：时间字段提取到「分钟」级统一比较

        原因：PG 存微秒（2026-07-27T08:21:34.884946），Coze 存储时会四舍五入
        到秒（2026-07-27 08:21:35 +0800 CST），秒级仍差 1 秒，导致同步永远判定
        "有变更"。统一到分钟级（YYYY-MM-DDTHH:MM）即可规避该舍入误差，对笔记
        同步而言分钟精度足够区分真实变更。

        PG 格式：2026-07-27T07:50:38.077466
        Coze 格式：2026-07-27 07:50:38 +0800 CST 或 2026-07-27T07:50:38.000Z
        """
        # None / 空串 统一为 ""
        if val is None or val == "" or str(val).lower() == "none":
            return ""
        if field_name in SyncService.TIME_FIELDS:
            import re
            # Coze 空时间哨兵：0001-01-01 08:00:00 +0800 CST → 视为空
            m = re.match(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", str(val).strip())
            if m:
                if m.group(1) == "0001-01-01":
                    return ""  # Coze 零值时间 = 空
                return f"{m.group(1)}T{m.group(2)}"
            return str(val)
        return str(val)

    @classmethod
    def _compare_objects(cls, pg_obj: dict, coze_obj: dict, fields: list[str]) -> dict | None:
        """比对两个记录的业务字段，返回差异 dict（无差异返回 None）

        所有值统一转为字符串，时间字段规范化后比较。
        """
        diff = {}
        for f in fields:
            pg_val = cls._normalize(str(pg_obj.get(f, "")), f)
            coze_val = cls._normalize(str(coze_obj.get(f, "")), f)
            if pg_val != coze_val:
                diff[f] = str(pg_obj.get(f, ""))
        return diff if diff else None

    # ── users 同步 ──

    async def _sync_users(self) -> dict:
        """同步 users 表，返回统计"""
        pg_all = await self.pg_users.find_all()
        coze_all = await self.coze_users.find_all()

        # 索引：{username: coze_record}
        coze_by_username: dict[str, dict] = {u["username"]: u for u in coze_all if u.get("username")}
        # 索引：{pg_id (from pg_id field): coze_record}
        coze_by_pg_id: dict[int, dict] = {}
        for u in coze_all:
            pg_id_val = u.get("pg_id")
            if pg_id_val:
                try:
                    coze_by_pg_id[int(pg_id_val)] = u
                except (ValueError, TypeError):
                    pass

        inserted = updated = deleted = skipped = 0

        # 遍历 PG 用户：匹配 / 更新 / 新增
        for pg_user in pg_all:
            username = pg_user["username"]
            coze_user = coze_by_username.get(username)
            if coze_user:
                # 已存在 → 比对业务字段
                diff = self._compare_objects(pg_user, coze_user, USER_BUSINESS_FIELDS)
                if diff:
                    # 更新（含 pg_id）
                    diff["pg_id"] = str(pg_user["id"])
                    await self.coze_users.update_by_coze_id(str(coze_user["id"]), diff)
                    updated += 1
                else:
                    # 同时也更新 pg_id 字段（可能首次同步时未设置）
                    coze_pg_id = coze_user.get("pg_id")
                    if not coze_pg_id or int(coze_pg_id) != pg_user["id"]:
                        await self.coze_users.update_by_coze_id(
                            str(coze_user["id"]), {"pg_id": str(pg_user["id"])}
                        )
                    skipped += 1
                # 记录映射
                self.user_id_map[pg_user["id"]] = str(coze_user["id"])
            else:
                # 不存在 → 插入
                fields = _user_to_coze_fields(pg_user)
                created = await self.coze_users.create_with_fields(fields)
                if created:
                    self.user_id_map[pg_user["id"]] = str(created["id"])
                    inserted += 1

        # Coze 多余用户 → 物理删除
        pg_username_set = {u["username"] for u in pg_all}
        for coze_user in coze_all:
            username = coze_user.get("username", "")
            if username and username not in pg_username_set:
                # 先删除该用户的笔记
                coze_user_id = str(coze_user["id"])
                coze_notes_all = await self.coze_notes.find_all_raw()
                for note in coze_notes_all:
                    if str(note.get("user_id", "")) == coze_user_id:
                        await self.coze_notes.delete_by_coze_id(str(note["id"]))
                # 再删除用户
                await self.coze_users.delete_by_coze_id(coze_user_id)
                deleted += 1

        return {"total": len(pg_all), "inserted": inserted, "updated": updated, "deleted": deleted, "skipped": skipped}

    # ── notes 同步 ──

    async def _sync_notes(self) -> dict:
        """同步 notes 表，返回统计（依赖 user_id_map）"""
        pg_all = await self.pg_notes.find_all_raw()
        coze_all = await self.coze_notes.find_all_raw()

        # 索引：{pg_id: coze_record}
        coze_by_pg_id: dict[int, dict] = {}
        for n in coze_all:
            pg_id_val = n.get("pg_id")
            if pg_id_val:
                try:
                    coze_by_pg_id[int(pg_id_val)] = n
                except (ValueError, TypeError):
                    pass

        inserted = updated = deleted = skipped = 0

        # 遍历 PG 笔记
        for pg_note in pg_all:
            pg_id = pg_note["id"]
            coze_note = coze_by_pg_id.get(pg_id)
            if coze_note:
                # 已存在 → 比对业务字段
                pg_converted = self._convert_note_for_coze(pg_note)
                diff = self._compare_objects(pg_converted, coze_note, NOTE_BUSINESS_FIELDS)
                if diff:
                    diff["pg_id"] = str(pg_id)
                    await self.coze_notes.update_by_coze_id(str(coze_note["id"]), diff)
                    updated += 1
                else:
                    # 确保 pg_id 一致
                    coze_pg_id = coze_note.get("pg_id")
                    if not coze_pg_id or int(coze_pg_id) != pg_id:
                        await self.coze_notes.update_by_coze_id(
                            str(coze_note["id"]), {"pg_id": str(pg_id)}
                        )
                    skipped += 1
            else:
                # 不存在 → 插入
                fields = _note_to_coze_fields(pg_note, self.user_id_map)
                created = await self.coze_notes.create_with_fields(fields)
                if created:
                    inserted += 1

        # Coze 多余笔记 → 物理删除
        pg_id_set = {n["id"] for n in pg_all}
        for coze_note in coze_all:
            pg_id_val = coze_note.get("pg_id")
            if pg_id_val:
                try:
                    if int(pg_id_val) not in pg_id_set:
                        await self.coze_notes.delete_by_coze_id(str(coze_note["id"]))
                        deleted += 1
                except (ValueError, TypeError):
                    pass

        return {"total": len(pg_all), "inserted": inserted, "updated": updated, "deleted": deleted, "skipped": skipped}

    def _convert_note_for_coze(self, pg_note: dict) -> dict:
        """将 PG 笔记转为 Coze 格式（user_id 转换为 coze_user_id）"""
        result = dict(pg_note)
        pg_user_id = pg_note.get("user_id", 0)
        coze_user_id = self.user_id_map.get(pg_user_id, "")
        if coze_user_id:
            result["user_id"] = coze_user_id
        return result

    # ── 主入口 ──

    async def sync(self) -> dict:
        """执行完整同步流程：users → 构建映射 → notes"""
        users_result = await self._sync_users()
        notes_result = await self._sync_notes()

        has_changes = any([
            users_result["inserted"] > 0,
            users_result["updated"] > 0,
            users_result["deleted"] > 0,
            notes_result["inserted"] > 0,
            notes_result["updated"] > 0,
            notes_result["deleted"] > 0,
        ])

        return {
            "users": users_result,
            "notes": notes_result,
            "has_changes": has_changes,
        }


# ── 字段构建辅助 ──


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _user_to_coze_fields(pg_user: dict) -> dict[str, str]:
    """将 PG 用户 dict 转为 Coze 插入字段"""
    return {
        "username": str(pg_user.get("username", "")),
        "password_hash": str(pg_user.get("password_hash", "")),
        "email": str(pg_user.get("email", "")),
        "created_at": str(pg_user.get("created_at", _now_iso())),
        "is_active": "1" if pg_user.get("is_active") else "0",
        "role": str(pg_user.get("role", "user")),
        "pg_id": str(pg_user.get("id", "")),
    }


def _note_to_coze_fields(pg_note: dict, user_id_map: dict[int, str]) -> dict[str, str]:
    """将 PG 笔记 dict 转为 Coze 插入字段（转换 user_id）"""
    pg_user_id = pg_note.get("user_id", 0)
    coze_user_id = user_id_map.get(pg_user_id, str(pg_user_id))

    return {
        "user_id": coze_user_id,
        "type": "1" if pg_note.get("type") == "folder" else "2",
        "title": str(pg_note.get("title", "")),
        "slug": str(pg_note.get("slug", "")),
        "content": str(pg_note.get("content", "")),
        "parent_id": str(pg_note.get("parent_id", 0)),
        "status": "2" if pg_note.get("status") == "published" else "1",
        "pinned": "1" if pg_note.get("pinned") else "0",
        "sort_order": str(pg_note.get("sort_order", 0)),
        "word_count": str(pg_note.get("word_count", 0)),
        "is_deleted": "1" if pg_note.get("is_deleted") else "0",
        "deleted_at": str(pg_note.get("deleted_at") or ""),
        "created_at": str(pg_note.get("created_at", _now_iso())),
        "updated_at": str(pg_note.get("updated_at", _now_iso())),
        "pg_id": str(pg_note.get("id", "")),
    }
