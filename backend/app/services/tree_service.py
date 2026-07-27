"""目录树服务：构建 folder + article 的嵌套树形结构"""
from collections import defaultdict
from app.repositories import get_note_repo


class TreeService:
    def __init__(self, note_repo=None):
        self.note_repo = note_repo if note_repo is not None else get_note_repo()

    async def build_tree(self, user_id: int | None = None) -> list[dict]:
        """构建完整目录树（folder 在前 + article 在后，按 sort_order/pinned/updated_at 排序）"""
        records = await self.note_repo.find_tree_records(user_id)

        # Map: parent_id → children
        tree_map: dict[int, list[dict]] = defaultdict(list)
        for r in records:
            pid = r.get("parent_id") or 0
            tree_map[pid].append({
                "id": r["id"],
                "type": r["type"],
                "name": r["title"],
                "slug": r.get("slug", ""),
                "parent_id": pid,
            })

        # 排序：folder 在前，article 在后
        def sort_key(node: dict) -> tuple:
            is_folder = 0 if node["type"] == "folder" else 1
            return (is_folder, node.get("sort_order", 0))

        for pid in tree_map:
            tree_map[pid].sort(key=sort_key)

        # 递归构建
        def build(parent_id: int = 0) -> list[dict]:
            children = tree_map.get(parent_id, [])
            result = []
            for node in children:
                item = {**node}
                sub = build(node["id"])
                if sub:
                    item["children"] = sub
                result.append(item)
            return result

        return build(0)
