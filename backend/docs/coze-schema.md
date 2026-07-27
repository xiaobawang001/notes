# Coze 数据库表结构设计 v2

> 按项目架构规则重构：从单表 `articles` 拆分为 `users` + `notes` 两张表，新增多用户认证支持。
>
> Coze 可用字段类型仅支持：`String`、`Integer`、`Time`、`Number`、`Boolean`。

---

## 一、users（用户表）

### Coze 自带默认字段

| 字段名 | 描述 | 类型 |
|--------|------|------|
| id | 数据的唯一标识（主键） | Integer |
| sys_platform | 数据产生或使用的渠道 | String |
| uuid | 用户唯一标识，由系统生成 | String |
| bstudio_create_time | 数据插入的时间 | Time |

### 业务字段

| 字段名 | Coze 字段类型 | 设为索引 | 是否必填 | 默认值 | 说明 |
|--------|-------------|---------|---------|--------|------|
| username | String | — | 是 | — | 用户名，应用层保证唯一 |
| password_hash | String | — | 是 | — | bcrypt 哈希后的密码 |
| email | String | — | 否 | — | 用户邮箱 |
| created_at | Time | — | 是 | — | 注册时间，ISO 8601 格式 |
| is_active | Integer | **是** | 是 | 1 | 账户状态：`1`=正常 / `0`=禁用 |
| role | String | — | 是 | "user" | 角色：`user`=普通用户 / `admin`=管理员 |

> **说明**：Coze 不支持 UNIQUE 约束，`username` 唯一性由应用层在注册时检查。
> 系统初始化时（users 表为空），第一个注册用户自动获得 `admin` 角色。

### 枚举映射

| 字段 | 值 | 含义 |
|------|----|------|
| is_active | `0` | 已禁用（不可登录） |
| is_active | `1` | 正常（可登录） |
| role | `"user"` | 普通用户 |
| role | `"admin"` | 管理员（可配置系统参数） |

### 接口传值

所有字段值以**字符串**形式传输：

```
username:     "zhangsan"
password_hash:"$2b$12$LJ3..."
email:        "zhang@example.com"
created_at:   "2026-07-27T10:00:00.000Z"
is_active:    "1"
role:         "user"        -- 或 "admin"
```

---

## 二、notes（笔记表）

融合规则要求的 Note 字段 + 保留原有树形层级扩展。

### Coze 自带默认字段

| 字段名 | 描述 | 类型 |
|--------|------|------|
| id | 数据的唯一标识（主键） | Integer |
| sys_platform | 数据产生或使用的渠道 | String |
| uuid | 用户唯一标识 | String |
| bstudio_create_time | 数据插入的时间 | Time |

### 业务字段

#### 规则要求的字段

| 字段名 | Coze 字段类型 | 设为索引 | 是否必填 | 默认值 | 说明 |
|--------|-------------|---------|---------|--------|------|
| user_id | Integer | **是** | 是 | — | 所属用户 ID（外键引用 users.id） |
| title | String | — | 是 | — | 标题 |
| content | String | — | 否 | — | Markdown 正文 |
| ai_summary | String | — | 否 | — | AI 生成的摘要 |
| created_at | Time | — | 是 | — | 创建时间 |
| updated_at | Time | — | 是 | — | 更新时间 |

#### 树形层级扩展字段

| 字段名 | Coze 字段类型 | 设为索引 | 是否必填 | 默认值 | 说明 |
|--------|-------------|---------|---------|--------|------|
| type | Integer | **是** | 是 | 2 | `1`=folder（目录）/ `2`=article（文章） |
| slug | String | — | 否 | — | URL 标识，文章必填 |
| parent_id | Integer | **是** | 否 | 0 | 父级记录 id，`0`=顶级 |
| status | Integer | **是** | 是 | 1 | `1`=draft / `2`=published |
| pinned | Integer | **是** | 是 | 0 | 置顶：`0`=否 / `1`=是 |
| sort_order | Integer | — | 否 | 0 | 同级排序权重，越小越靠前 |
| word_count | Integer | — | 否 | 0 | 字数统计 |
| is_deleted | Integer | **是** | 是 | 0 | 软删除：`0`=正常 / `1`=已删除 |
| deleted_at | Time | — | 否 | — | 软删除时间戳 |

### 枚举映射

| 字段 | 值 | 含义 |
|------|-----|------|
| type | `1` | folder（目录） |
| type | `2` | article（文章） |
| status | `1` | draft（草稿） |
| status | `2` | published（已发布） |
| pinned | `0` | 未置顶 |
| pinned | `1` | 已置顶 |
| is_deleted | `0` | 正常 |
| is_deleted | `1` | 已软删除 |

### type 字段说明

- `type = 1`（folder）：目录/文件夹，`content`/`slug` 可为空
- `type = 2`（article）：文章，`title` 和 `slug` 必填，`parent_id` 指向所属目录

### parent_id 字段说明

`parent_id` 存储父级记录 `id`，`0` 表示顶级根节点。

示例数据：
```
| id  | user_id | type | title      | slug           | parent_id | status |
|-----|---------|------|------------|----------------|-----------|--------|
| 101 | 1       | 1    | 服务器运维  |                | 0         | 2      |
| 102 | 1       | 1    | docker     |                | 101       | 2      |
| 103 | 1       | 2    | Docker安装  | docker-install | 102       | 2      |
```

### sort_order 排序优先级

```
pinned = 1 优先
  → sort_order 越小越靠前
    → updated_at 越新越靠前
```

### 接口传值

所有字段值以**字符串**形式传输：

```
user_id:      "1"
type:         "2"
title:        "Docker 安装指南"
slug:         "docker-install"
content:      "# Docker 安装\n\n..."
ai_summary:   "本文介绍..."
parent_id:    "102"
status:       "2"
pinned:       "0"
sort_order:   "0"
word_count:   "1234"
is_deleted:   "0"
created_at:   "2026-07-27T10:00:00.000Z"
updated_at:   "2026-07-27T10:00:00.000Z"
```

---

## 三、settings（系统配置表）

管理员可在线更新的配置项，存储于 Coze 多维表格。

### Coze 自带默认字段

| 字段名 | 描述 | 类型 |
|--------|------|------|
| id | 数据的唯一标识（主键） | Integer |
| sys_platform | 数据产生或使用的渠道 | String |
| uuid | 用户唯一标识，由系统生成 | String |
| bstudio_create_time | 数据插入的时间 | Time |

### 业务字段

| 字段名 | Coze 字段类型 | 设为索引 | 是否必填 | 默认值 | 说明 |
|--------|-------------|---------|---------|--------|------|
| key | String | **是** | 是 | — | 配置键名（如 "COZE_TOKEN"） |
| value | String | — | 是 | — | 配置值 |
| updated_at | Time | — | 是 | — | 更新时间 |

### 预置键名

| key | 说明 |
|-----|------|
| COZE_TOKEN | Coze 个人访问令牌（每月更新） |
| COZE_BASE_URL | Coze API 地址 |
| COZE_USERS_DATABASE_ID | users 表 database ID |
| COZE_NOTES_DATABASE_ID | notes 表 database ID |

### 应用层约束
1. **key 唯一性**：同 key 只能有一条记录，更新时 upsert
2. **管理员专属**：只有 role=admin 的用户可读写此表
3. **配置刷新**：更新后立即刷新内存缓存，不重启服务

---

## 四、在 Coze 平台创建表

### 操作步骤

1. 登录 [Coze 控制台](https://www.coze.cn)
2. 进入「个人空间 → 资源 → 知识库 → 多维表格」
3. 点击「创建多维表格」

### users 表

- 表格名称：`users`
- 字段列表（手动逐一添加，去掉「用户端可输入」勾选）：

| 字段名 | 类型 | 设为索引 |
|--------|------|---------|
| username | 文本（String） | 否 |
| password_hash | 文本（String） | 否 |
| email | 文本（String） | 否 |
| created_at | 时间（Time） | 否 |
| is_active | 整数（Integer） | **是** |
| role | 文本（String） | 否 |

### notes 表

- 表格名称：`notes`
- 字段列表：

| 字段名 | 类型 | 设为索引 |
|--------|------|---------|
| user_id | 整数（Integer） | **是** |
| type | 整数（Integer） | **是** |
| title | 文本（String） | 否 |
| slug | 文本（String） | 否 |
| content | 文本（String） | 否 |
| ai_summary | 文本（String） | 否 |
| parent_id | 整数（Integer） | **是** |
| status | 整数（Integer） | **是** |
| pinned | 整数（Integer） | **是** |
| sort_order | 整数（Integer） | 否 |
| word_count | 整数（Integer） | 否 |
| is_deleted | 整数（Integer） | **是** |
| deleted_at | 时间（Time） | 否 |
| created_at | 时间（Time） | 否 |
| updated_at | 时间（Time） | 否 |

### settings 表

- 表格名称：`settings`
- 字段列表：

| 字段名 | 类型 | 设为索引 |
|--------|------|---------|
| key | 文本（String） | **是** |
| value | 文本（String） | 否 |
| updated_at | 时间（Time） | 否 |

### 获取 Database ID

创建完成后，进入表格 → 右上角「...」→「查看 API」→ 复制 URL 中的 database ID。

> **注意**：settings 表的 database ID 需通过环境变量 `COZE_SETTINGS_DATABASE_ID` 或管理员后台配置。

---

## 五、数据迁移（从 articles 到 notes）

### 字段变更对照

| 旧字段（articles） | 新字段（notes） | 变更说明 |
|--------------------|-----------------|---------|
| — | `user_id` | **新增**，所有旧数据设为 `1` |
| `summary` | `ai_summary` | 重命名 |
| `is_deleted` | `is_deleted` | 不变 |
| `deleted_at` | `deleted_at` | 不变 |
| `type` | `type` | 不变 |
| `title` | `title` | 不变 |
| `slug` | `slug` | 不变 |
| `content` | `content` | 不变 |
| `parent_id` | `parent_id` | 类型不变，空值改为 `0` |
| `status` | `status` | 不变 |
| `pinned` | `pinned` | 不变 |
| `sort_order` | `sort_order` | 不变 |
| `word_count` | `word_count` | 不变 |
| `created_at` | `created_at` | 不变 |
| `updated_at` | `updated_at` | 不变 |

### 迁移脚本说明

迁移脚本位于 `backend/scripts/migrate_v1_to_v2.py`，执行：
1. 从旧 `articles` 表查询所有记录
2. 添加 `user_id = 1`
3. `summary` → `ai_summary`
4. 空 `parent_id` → `"0"`
5. 批量插入 `notes` 表

---

## 六、应用层约束

Coze 不支持外键和复杂约束，以下逻辑需在代码中处理：

1. **username 唯一性**：注册时应用层检查 users 表是否已存在同名用户
2. **type 枚举**：只能是 `1`(folder) 或 `2`(article)
3. **status 枚举**：只能是 `1`(draft) 或 `2`(published)
4. **slug 唯一性**：同用户下文章 slug 唯一
5. **parent_id 合法性**：必须指向 `type=1` 且 `is_deleted=0` 的记录
6. **目录 status 强制**：folder 创建/修改时 status 强制为 `published`
7. **软删除**：所有查询默认加 `is_deleted = 0`
8. **越权防护**：所有查询必须带 `user_id` 过滤
9. **删除目录**：递归删除所有子节点

---

## 七、主要查询场景

| 功能 | 查询条件 |
|------|---------|
| 构建目录树 | `is_deleted=0` AND `type=1`(folder) OR (`type=2` AND `status=2`) |
| 公开文章列表 | `type=2` AND `status=2` AND `is_deleted=0` |
| 用户笔记列表 | `user_id=?` AND `is_deleted=0` |
| 文章详情 | `slug=?` AND `is_deleted=0` |
| 全文搜索 | `type=2` AND `status=2` AND `is_deleted=0` AND (title/content/ai_summary 包含关键词) |

---

## 八、环境变量

```env
# Coze API
COZE_TOKEN=你的 Coze 个人访问令牌
COZE_BASE_URL=https://api.coze.cn
COZE_USERS_DATABASE_ID=users 表的数据库 ID
COZE_NOTES_DATABASE_ID=notes 表的数据库 ID
COZE_SETTINGS_DATABASE_ID=settings 表的数据库 ID

# JWT
SECRET_KEY=你的 JWT 密钥（至少 32 字符）
```
