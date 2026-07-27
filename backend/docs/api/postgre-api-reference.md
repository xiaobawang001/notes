# Blog API 接口文档 — PostgreSQL 模式

> **后端:** PostgreSQL (asyncpg)  |  **基础 URL:** `http://localhost:8000/postgre/v1`
>
> 启动命令: `DB_MODE=postgres uvicorn main:app`

---

## 1. 概述

### 1.1 统一响应格式

所有接口返回统一的 JSON 结构：

**成功响应:**
```json
{
  "code": 0,
  "data": { ... },
  "msg": "success"
}
```

**错误响应:**
```json
{
  "detail": {
    "code": 400,
    "msg": "错误描述"
  }
}
```

### 1.2 认证方式

需要认证的接口在请求头中携带 JWT Token：

```
Authorization: Bearer <token>
```

Token 通过 `/postgre/v1/auth/register` 或 `/postgre/v1/auth/login` 获取，有效期 24 小时，可通过 `/postgre/v1/auth/refresh` 刷新。

### 1.3 接口总览

| # | 方法 | 路径 | 认证 | 说明 |
|---|------|------|------|------|
| 1 | POST | `/postgre/v1/auth/register` | 无 | 用户注册 |
| 2 | POST | `/postgre/v1/auth/login` | 无 | 用户登录 |
| 3 | POST | `/postgre/v1/auth/refresh` | 无* | 刷新 Token |
| 4 | GET | `/postgre/v1/notes` | 可选 | 笔记列表 |
| 5 | GET | `/postgre/v1/notes/categories` | 可选 | 目录树 |
| 6 | GET | `/postgre/v1/notes/search` | 可选 | 全文搜索 |
| 7 | GET | `/postgre/v1/notes/{id}` | 无 | 按 ID 获取笔记 |
| 8 | GET | `/postgre/v1/notes/slug/{slug}` | 无 | 按 slug 获取笔记 |
| 9 | POST | `/postgre/v1/notes` | **必须** | 创建笔记 |
| 10 | PUT | `/postgre/v1/notes/{id}` | **必须** | 更新笔记 |
| 11 | DELETE | `/postgre/v1/notes/{id}` | **必须** | 删除笔记 |

> **健康检查:** `GET /postgre/v1/health` → `{"code":0,"msg":"ok","db_mode":"postgres"}`

---

## 2. 认证接口

### 2.1 用户注册

```
POST /postgre/v1/auth/register
```

**Request Body:**

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `username` | string | **是** | 3-50 字符，唯一 | 用户名 |
| `password` | string | **是** | 6-100 字符 | 密码 |
| `email` | string | 否 | 最长 200 字符 | 邮箱 |

**示例：**
```json
{
  "username": "alice",
  "password": "MyPass123",
  "email": "alice@example.com"
}
```

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user_id": 1,
    "username": "alice",
    "role": "user"
  },
  "msg": "注册成功"
}
```

> **注意:** PostgreSQL 模式下 `user_id` 为 `SERIAL` 自增整数（从 1 开始）。

**错误响应:**

| code | 说明 |
|------|------|
| 400 | 用户名已存在（UNIQUE 约束） |
| 422 | 参数校验失败 |
| 500 | 服务器内部错误 |

---

### 2.2 用户登录

```
POST /postgre/v1/auth/login
```

**Request Body:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | **是** | 用户名 |
| `password` | string | **是** | 密码 |

**示例：**
```json
{
  "username": "alice",
  "password": "MyPass123"
}
```

**成功响应 (200):** 同 2.1 注册响应。

**错误响应:**

| code | 说明 |
|------|------|
| 400 | 用户名或密码错误 / 账户已被禁用 |

---

### 2.3 刷新 Token

```
POST /postgre/v1/auth/refresh
```

**Request Body:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `token` | string | **是** | 当前持有的 JWT Token |

**示例：**
```json
{
  "token": "eyJhbGciOi..."
}
```

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOi...(新Token)",
    "token_type": "bearer",
    "user_id": 1,
    "username": "alice",
    "role": "user"
  },
  "msg": "刷新成功"
}
```

**错误响应:**

| code | 说明 |
|------|------|
| 401 | Token 无效或已过期 / 用户不存在 |

---

## 3. 笔记接口

### 3.1 笔记列表

```
GET /postgre/v1/notes
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|------|------|------|--------|------|------|
| `type` | string | 否 | — | `folder` / `article` | 按类型过滤 |
| `status` | string | 否 | — | `draft` / `published` | 按状态过滤 |
| `parent_id` | int | 否 | — | — | 按父目录 ID 过滤 |
| `search` | string | 否 | — | — | 关键字搜索 |
| `page` | int | 否 | 1 | ≥ 1 | 页码 |
| `page_size` | int | 否 | 20 | 1-500 | 每页数量 |

> **认证:** 可选。已登录返回自己的笔记，未登录仅返回公开笔记。
> **排序:** pinned DESC → sort_order ASC → updated_at DESC

**示例：**
```
GET /postgre/v1/notes?type=article&status=published&page=1&page_size=10
```

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 4,
        "user_id": 1,
        "type": "article",
        "title": "我的第一篇文章",
        "slug": "my-first-post",
        "content": "# Hello World\n...",
        "parent_id": 0,
        "status": "published",
        "pinned": false,
        "sort_order": 0,
        "word_count": 120,
        "is_deleted": false,
        "deleted_at": null,
        "created_at": "2026-07-27T06:38:42",
        "updated_at": "2026-07-27T06:38:42"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  },
  "msg": "success"
}
```

> **注意:** PostgreSQL 模式下 `id` 为 SERIAL 自增整数，时间格式为 ISO 8601（无时区）。

---

### 3.2 目录树

```
GET /postgre/v1/notes/categories
```

> **认证:** 可选。登录则按用户过滤，未登录返回所有公开目录。

**示例：**
```
GET /postgre/v1/notes/categories
```

**成功响应 (200):**
```json
{
  "code": 0,
  "data": [
    {
      "id": 3,
      "type": "folder",
      "name": "技术笔记",
      "slug": "",
      "parent_id": 0,
      "children": [
        {
          "id": 5,
          "type": "folder",
          "name": "Python",
          "slug": "",
          "parent_id": 3,
          "children": []
        }
      ]
    }
  ],
  "msg": "success"
}
```

---

### 3.3 全文搜索

```
GET /postgre/v1/notes/search
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `q` | string | **是** | 最少 1 字符 | 搜索关键词 |

> **认证:** 可选。登录则限定搜索自己的笔记。
> **搜索算法:** PostgreSQL `ILIKE` 不区分大小写的模糊匹配（title + content）。

**示例：**
```
GET /postgre/v1/notes/search?q=Python
```

**成功响应 (200):**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 4,
        "title": "Python 入门指南",
        "slug": "python-guide",
        "updated_at": "2026-07-27T06:38:42"
      }
    ],
    "total": 1
  },
  "msg": "success"
}
```

---

### 3.4 按 ID 获取笔记

```
GET /postgre/v1/notes/{note_id}
```

**Path Parameters:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `note_id` | int | 笔记 ID（SERIAL 整数） |

**示例：**
```
GET /postgre/v1/notes/4
```

**成功响应 (200):** 同 3.1 列表项格式。

**错误响应:** 404 — 笔记不存在

---

### 3.5 按 slug 获取笔记

```
GET /postgre/v1/notes/slug/{slug}
```

**Path Parameters:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `slug` | string | 文章 URL 标识 |

**示例：**
```
GET /postgre/v1/notes/slug/my-first-post
```

**成功响应 (200):** 同 3.4。

**错误响应:** 404 — 文章不存在

---

### 3.6 创建笔记

```
POST /postgre/v1/notes
```

> **认证:** 必须登录（`Authorization: Bearer <token>`）
> **状态码:** 201 Created

**Request Body:**

| 字段 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|------|------|------|--------|------|------|
| `type` | string | 否 | `article` | `folder` / `article` | 笔记类型 |
| `title` | string | **是** | — | 1-500 字符 | 标题 |
| `slug` | string | 否 | — | 最长 200 字符 | URL 标识 |
| `content` | string | 否 | — | — | Markdown 正文 |
| `parent_id` | int | 否 | 0 | — | 父目录 ID |
| `status` | string | 否 | `published` | `draft` / `published` | 发布状态 |
| `pinned` | bool | 否 | `false` | — | 是否置顶 |
| `sort_order` | int | 否 | 0 | — | 排序权重 |

**示例：**
```json
{
  "type": "article",
  "title": "我的第一篇文章",
  "slug": "my-first-post",
  "content": "# Hello World\n\n这是我的第一篇文章。",
  "parent_id": 3,
  "status": "published"
}
```

**成功响应 (201):**
```json
{
  "code": 0,
  "data": {
    "id": 4,
    "user_id": 1,
    "type": "article",
    "title": "我的第一篇文章",
    "slug": "my-first-post",
    "content": "# Hello World\n\n这是我的第一篇文章。",
    "parent_id": 3,
    "status": "published",
    "pinned": false,
    "sort_order": 0,
    "word_count": 15,
    "is_deleted": false,
    "deleted_at": null,
    "created_at": "2026-07-27T06:38:42",
    "updated_at": "2026-07-27T06:38:42"
  },
  "msg": "创建成功"
}
```

**错误响应:**

| code | 说明 |
|------|------|
| 400 | parent_id 无效（不是有效目录） |
| 401 | 未登录 |
| 500 | 服务器内部错误 |

---

### 3.7 更新笔记

```
PUT /postgre/v1/notes/{note_id}
```

> **认证:** 必须登录，且只能更新自己的笔记。

**Path Parameters:** `note_id` — 笔记 ID

**Request Body:** 所有字段均为可选，仅提交需要更新的字段。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `type` | string | `folder` / `article` | 笔记类型 |
| `title` | string | 1-500 字符 | 标题 |
| `slug` | string | 最长 200 字符 | URL 标识 |
| `content` | string | — | Markdown 正文 |
| `parent_id` | int | — | 父目录 ID |
| `status` | string | `draft` / `published` | 发布状态 |
| `pinned` | bool | — | 是否置顶 |
| `sort_order` | int | — | 排序权重 |

**示例：**
```json
{
  "title": "我的第一篇文章 (已更新)",
  "content": "## 更新后的内容",
  "status": "published"
}
```

**成功响应 (200):** 返回更新后的笔记完整数据。

**错误响应:**

| code | 说明 |
|------|------|
| 401 | 未登录 |
| 403 | 无权编辑他人的笔记 |
| 404 | 笔记不存在 |

---

### 3.8 删除笔记

```
DELETE /postgre/v1/notes/{note_id}
```

> **认证:** 必须登录，且只能删除自己的笔记。
> 删除目录时会递归软删除所有子节点。

**Path Parameters:** `note_id` — 笔记 ID

**示例：**
```
DELETE /postgre/v1/notes/4
```

**成功响应 (200):**
```json
{
  "code": 0,
  "data": null,
  "msg": "删除成功"
}
```

**错误响应:**

| code | 说明 |
|------|------|
| 401 | 未登录 |
| 403 | 无权删除他人的笔记 |
| 404 | 笔记不存在 |

---

## 4. 数据模型

### 4.1 TokenResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| `token` | string | JWT access token |
| `token_type` | string | 固定值 `"bearer"` |
| `user_id` | int | 用户 ID（SERIAL 自增整数） |
| `username` | string | 用户名 |
| `role` | string | `user` 或 `admin` |

### 4.2 NoteItem

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 笔记 ID（SERIAL 自增整数） |
| `user_id` | int | 所属用户 ID |
| `type` | string | `folder` 或 `article` |
| `title` | string | 标题 |
| `slug` | string | URL 标识（文章专有） |
| `content` | string | Markdown 正文 |
| `parent_id` | int | 父目录 ID，0=顶级 |
| `status` | string | `draft` 或 `published` |
| `pinned` | bool | 是否置顶 |
| `sort_order` | int | 同级排序权重 |
| `word_count` | int | 正文字数 |
| `is_deleted` | bool | 是否已软删除 |
| `deleted_at` | string \| null | 软删除时间（ISO 8601） |
| `created_at` | string | 创建时间（ISO 8601） |
| `updated_at` | string | 更新时间（ISO 8601） |

### 4.3 CategoryTreeItem

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 目录 ID |
| `type` | string | `folder` |
| `name` | string | 目录名（映射自 `title`） |
| `slug` | string | URL 标识 |
| `parent_id` | int | 父目录 ID |
| `children` | CategoryTreeItem[] | 子目录列表 |

---

## 5. 错误码速查

| HTTP | code | msg |
|------|------|-----|
| 400 | 400 | 用户名已存在 |
| 400 | 400 | 用户名或密码错误 |
| 400 | 400 | 账户已被禁用 |
| 400 | 400 | 参数校验错误（parent_id/slug） |
| 401 | 401 | 请先登录 |
| 401 | 401 | Token 无效或已过期 |
| 403 | 403 | 无权编辑他人的笔记 |
| 403 | 403 | 需要管理员权限 |
| 404 | 404 | 文章不存在 |
| 404 | 404 | 笔记不存在 |
| 422 | — | 请求参数校验失败（FastAPI 自动处理） |
| 500 | 500 | 服务器内部错误 |

---

## 6. PostgreSQL 模式特性

| 特性 | 说明 |
|------|------|
| 数据存储 | PostgreSQL（SQLAlchemy 2.0 async + asyncpg） |
| ID 格式 | SERIAL 自增整数（1, 2, 3, ...） |
| 时间格式 | `"YYYY-MM-DDTHH:MM:SS"`（ISO 8601，无时区） |
| 全文搜索 | PostgreSQL `ILIKE`（不区分大小写） |
| 写入确认 | 事务保证，INSERT/UPDATE/DELETE 实时生效 |
| 查询能力 | 支持复杂 SQL、JOIN、聚合、分页 |
| 约束 | 数据库层 UNIQUE + FOREIGN KEY + INDEX |
| 连接池 | asyncpg pool_size=10, max_overflow=20 |

---

## 7. Coze ↔ PostgreSQL 切换

| 项目 | Coze 模式 | PostgreSQL 模式 |
|------|-----------|-----------------|
| 环境变量 | `DB_MODE=coze` | `DB_MODE=postgres` |
| API 前缀 | `/coze/v1` | `/postgre/v1` |
| user_id 格式 | 长整数（~19 位） | 自增整数（1, 2, 3...） |
| 建表 | 无需（Coze 托管） | 首次启动自动建表 |
| 搜索 | LIKE 模糊匹配 | ILIKE 不区分大小写 |
| 事务 | 不支持 | 完整 ACID 事务 |
