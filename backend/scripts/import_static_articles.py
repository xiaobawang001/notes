"""
从 xiaobawang001.github.io-master 静态博客导入文章到数据库
用法: python3 import_static_articles.py
前置条件: 后端运行中, 管理员用户存在
"""

import os
import sys
import json
import re
import yaml
import urllib.request

# ── 配置 ──
API_BASE = "http://localhost:3000/postgre/v1"
USERNAME = "xiaobawang001"
PASSWORD = "Qnzy.134650"
STATIC_DIR = "/home/bobo/myProj/xiaobawang001.github.io-master/docs"
SIDEBAR_FILE = "/home/bobo/myProj/xiaobawang001.github.io-master/sidebar-tree.yaml"
USER_ID = 18  # 已知管理员 ID

# ── 辅助函数 ──
def api_call(method, path, data=None, token=None):
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  [错误] {method} {path} -> {e.code}: {err}")
        return None


def get_title(filepath):
    """从 markdown 文件中提取第一个 h1 标题"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # 回退到文件名
    return os.path.splitext(os.path.basename(filepath))[0]


def get_content(filepath):
    """读取 markdown 全文"""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def get_slug(rel_path):
    """从相对路径生成 slug"""
    return rel_path.replace("\\", "/").replace(".md", "")


def create_folder(token, title, parent_id=0):
    """创建目录节点"""
    data = {"type": "folder", "title": title, "parent_id": parent_id, "status": "published"}
    result = api_call("POST", "/notes", data, token)
    if result and result.get("code") == 0:
        note_id = result["data"]["id"]
        print(f"  [目录] '{title}' (parent={parent_id}) -> id={note_id}")
        return note_id
    return None


def create_article(token, title, slug, content, parent_id):
    """创建文章节点"""
    data = {
        "type": "article",
        "title": title,
        "slug": slug,
        "content": content,
        "parent_id": parent_id,
        "status": "published",
    }
    result = api_call("POST", "/notes", data, token)
    if result and result.get("code") == 0:
        note_id = result["data"]["id"]
        print(f"  [文章] '{title}' (/{slug}) -> id={note_id}")
        return note_id
    return None


# ── 主流程 ──
def main():
    # 1. 登录获取 token
    print(">>> 登录获取 Token...")
    login_result = api_call("POST", "/auth/login", {"username": USERNAME, "password": PASSWORD})
    if not login_result or login_result.get("code") != 0:
        print("登录失败，请检查用户名密码")
        sys.exit(1)
    token = login_result["data"]["token"]
    print(f"  Token 获取成功 (username={USERNAME})")

    # 2. 读取 sidebar-tree.yaml
    print(f"\n>>> 读取侧边栏配置: {SIDEBAR_FILE}")
    with open(SIDEBAR_FILE, "r", encoding="utf-8") as f:
        sidebar_tree = yaml.safe_load(f)
    print(f"  解析到 {len(sidebar_tree)} 个顶级分类")

    # 3. 遍历树，创建目录和文章
    # 先清除已有笔记（避免重复导入）
    print(f"\n>>> 注意：请确认数据库未包含冲突数据，或运行删除脚本清理")
    print(f">>> 开始导入...\n")

    created_ids = {}  # {category_path: db_id}

    for top_cat_name, children in sidebar_tree.items():
        # 创建顶级目录
        top_id = create_folder(token, top_cat_name)
        if top_id is None:
            print(f"  [跳过] 顶级目录 '{top_cat_name}' 创建失败")
            continue
        created_ids[top_cat_name] = top_id

        if isinstance(children, dict):
            # 有子分类
            for sub_cat_name, articles in children.items():
                sub_cat_path = f"{top_cat_name}/{sub_cat_name}"
                sub_id = create_folder(token, sub_cat_name, parent_id=top_id)
                if sub_id is None:
                    print(f"  [跳过] 子目录 '{sub_cat_name}' 创建失败")
                    continue
                created_ids[sub_cat_path] = sub_id

                for article_title in articles:
                    rel_md = f"{sub_cat_path}/{article_title}.md"
                    filepath = os.path.join(STATIC_DIR, rel_md)
                    if not os.path.exists(filepath):
                        print(f"  [警告] 文件不存在: {filepath}")
                        continue
                    title = get_title(filepath)
                    content = get_content(filepath)
                    slug = get_slug(rel_md)
                    create_article(token, title, slug, content, parent_id=sub_id)
        elif isinstance(children, list):
            # 直接是文章列表
            for article_title in children:
                rel_md = f"{top_cat_name}/{article_title}.md"
                filepath = os.path.join(STATIC_DIR, rel_md)
                if not os.path.exists(filepath):
                    print(f"  [警告] 文件不存在: {filepath}")
                    continue
                title = get_title(filepath)
                content = get_content(filepath)
                slug = get_slug(rel_md)
                create_article(token, title, slug, content, parent_id=top_id)

    # 额外导入 使用指南/发布新文章.md（被侧边栏排除但存在）
    extra_file = os.path.join(STATIC_DIR, "使用指南/发布新文章.md")
    if os.path.exists(extra_file):
        print(f"\n>>> 额外导入: 使用指南/发布新文章")
        title = get_title(extra_file)
        content = get_content(extra_file)
        slug = "使用指南/发布新文章"
        parent_id = created_ids.get("使用指南", 0)
        create_article(token, title, slug, content, parent_id=parent_id)

    print(f"\n>>> 导入完成！")


if __name__ == "__main__":
    main()
