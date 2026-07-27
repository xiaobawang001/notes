# PostgreSQL 数据库表结构设计 v3

> 与 Coze 多维表格字段严格对齐，确保 PG → Coze 数据同步零出错。
>
> 本设计为 PostgreSQL 原生表，Coze 侧对应的 `pg_id` 字段用于跨平台记录匹配。

---

## 一、users（用户表）

### DDL

```sql
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(100) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    email           VARCHAR(200),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active       INTEGER NOT NULL DEFAULT 1,
    role            VARCHAR(20) NOT NULL DEFAULT 'user'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.id IS '主键（BIGINT 自增）';
COMMENT ON COLUMN users.username IS '用户名（应用层保证唯一）';
COMMENT ON COLUMN users.password_hash IS 'bcrypt 哈希密码';
COMMENT ON COLUMN users.email IS '邮箱（可选）';
COMMENT ON COLUMN users.created_at IS '注册时间';
COMMENT ON COLUMN users.is_active IS '0=禁用, 1=正常';
COMMENT ON COLUMN users.role IS 'user=普通用户, admin=管理员';
```

### 字段说明

| 字段 | PG 类型 | 约束 | 默认值 | 说明 |
|------|---------|------|--------|------|
| id | BIGSERIAL | PK | 自增 | 主键，对应 Coze `pg_id` |
| username | VARCHAR(100) | UNIQUE, NOT NULL | — | 用户名 |
| password_hash | VARCHAR(255) | NOT NULL | — | bcrypt 哈希 |
| email | VARCHAR(200) | — | NULL | 邮箱 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 注册时间 |
| is_active | INTEGER | INDEX | 1 | 0=禁用, 1=正常 |
| role | VARCHAR(20) | — | "user" | user/admin |

### 枚举

| 字段 | 值 | 含义 |
|------|----|------|
| is_active | `0` | 已禁用 |
| is_active | `1` | 正常 |
| role | `"user"` | 普通用户 |
| role | `"admin"` | 管理员 |

---

## 二、notes（笔记表）

### DDL

```sql
CREATE TABLE IF NOT EXISTS notes (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    type            INTEGER NOT NULL DEFAULT 2,
    title           VARCHAR(500) NOT NULL,
    slug            VARCHAR(200),
    content         TEXT,
    parent_id       BIGINT NOT NULL DEFAULT 0,
    status          INTEGER NOT NULL DEFAULT 1,
    pinned          INTEGER NOT NULL DEFAULT 0,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    word_count      INTEGER NOT NULL DEFAULT 0,
    is_deleted      INTEGER NOT NULL DEFAULT 0,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes (user_id);
CREATE INDEX IF NOT EXISTS idx_notes_type ON notes (type);
CREATE INDEX IF NOT EXISTS idx_notes_parent_id ON notes (parent_id);
CREATE INDEX IF NOT EXISTS idx_notes_status ON notes (status);
CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes (pinned);
CREATE INDEX IF NOT EXISTS idx_notes_is_deleted ON notes (is_deleted);

COMMENT ON TABLE notes IS '笔记表（含目录和文章）';
COMMENT ON COLUMN notes.id IS '主键（BIGINT 自增），对应 Coze pg_id';
COMMENT ON COLUMN notes.user_id IS '所属用户 ID（外键引用 users.id）';
COMMENT ON COLUMN notes.type IS '1=folder, 2=article';
COMMENT ON COLUMN notes.title IS '标题';
COMMENT ON COLUMN notes.slug IS 'URL 标识（文章必填）';
COMMENT ON COLUMN notes.content IS 'Markdown 正文';
COMMENT ON COLUMN notes.parent_id IS '父级 ID（BIGINT）, 0=顶级';
COMMENT ON COLUMN notes.status IS '1=draft, 2=published';
COMMENT ON COLUMN notes.pinned IS '0=否, 1=是';
COMMENT ON COLUMN notes.sort_order IS '排序权重（越小越靠前）';
COMMENT ON COLUMN notes.word_count IS '字数统计';
COMMENT ON COLUMN notes.is_deleted IS '0=正常, 1=已删除';
COMMENT ON COLUMN notes.deleted_at IS '软删除时间戳';
COMMENT ON COLUMN notes.created_at IS '创建时间';
COMMENT ON COLUMN notes.updated_at IS '更新时间';
```

### 字段说明

| 字段 | PG 类型 | 约束 | 默认值 | 说明 |
|------|---------|------|--------|------|
| id | BIGSERIAL | PK | 自增 | 主键，对应 Coze `pg_id` |
| user_id | BIGINT | FK → users.id | — | 所属用户 |
| type | INTEGER | INDEX | 2 | 1=folder, 2=article |
| title | VARCHAR(500) | NOT NULL | — | 标题 |
| slug | VARCHAR(200) | — | NULL | URL 标识 |
| content | TEXT | — | NULL | Markdown 正文 |
| parent_id | BIGINT | INDEX | 0 | 0=顶级 |
| status | INTEGER | INDEX | 1 | 1=draft, 2=published |
| pinned | INTEGER | INDEX | 0 | 0=否, 1=是 |
| sort_order | INTEGER | — | 0 | 排序权重 |
| word_count | INTEGER | — | 0 | 字数 |
| is_deleted | INTEGER | INDEX | 0 | 0=正常, 1=已删除 |
| deleted_at | TIMESTAMP | — | NULL | 软删除时间 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间 |

### 枚举

| 字段 | 值 | 含义 |
|------|----|------|
| type | `1` | folder（目录） |
| type | `2` | article（文章） |
| status | `1` | draft |
| status | `2` | published |
| pinned | `0` | 未置顶 |
| pinned | `1` | 已置顶 |
| is_deleted | `0` | 正常 |
| is_deleted | `1` | 已删除 |

### 排序规则

```
pinned = 1 优先
  → sort_order 越小越靠前
    → updated_at 越新越靠前
```

---

## 三、与 Coze 表的字段映射

### users 映射

| PG 字段 | Coze 业务字段 | 同步方向 | 说明 |
|---------|-------------|----------|------|
| id | pg_id | PG → Coze | PG 主键写入 Coze `pg_id` 字段 |
| username | username | PG → Coze | 匹配键 |
| password_hash | password_hash | PG → Coze | bcrypt 哈希 |
| email | email | PG → Coze | 直接映射 |
| created_at | created_at | PG → Coze | ISO 8601 |
| is_active (0/1) | is_active ("0"/"1") | PG → Coze | int ↔ str |
| role | role | PG → Coze | 直接映射 |

### notes 映射

| PG 字段 | Coze 业务字段 | 同步方向 | 说明 |
|---------|-------------|----------|------|
| id | pg_id | PG → Coze | PG 主键写入 Coze `pg_id` 字段 |
| user_id | user_id | PG → Coze | **需要转换**：PG user_id → Coze user record id |
| type (1/2) | type ("1"/"2") | PG → Coze | int ↔ str |
| title | title | PG → Coze | 直接映射 |
| slug | slug | PG → Coze | 直接映射 |
| content | content | PG → Coze | 直接映射 |
| parent_id | parent_id | PG → Coze | int ↔ str，0=顶级 |
| status (1/2) | status ("1"/"2") | PG → Coze | int ↔ str |
| pinned (0/1) | pinned ("0"/"1") | PG → Coze | int ↔ str |
| sort_order | sort_order | PG → Coze | int ↔ str |
| word_count | word_count | PG → Coze | int ↔ str |
| is_deleted (0/1) | is_deleted ("0"/"1") | PG → Coze | int ↔ str |
| deleted_at | deleted_at | PG → Coze | ISO 8601 |
| created_at | created_at | PG → Coze | ISO 8601 |
| updated_at | updated_at | PG → Coze | ISO 8601 |

### Coze 平台自有字段（不参与同步）

| 字段 | 来源 | 说明 |
|------|------|------|
| id | Coze 自动 | 记录主键（自增） |
| sys_platform | Coze 自动 | 数据渠道 |
| uuid | Coze 自动 | 系统 UUID |
| bstudio_create_time | Coze 自动 | 记录插入时间 |

---

## 四、Coze 表新增字段（同步必需）

为确保 PG → Coze 同步时能精确匹配记录，Coze 两张表需新增 `pg_id` 字段：

### users 表新增

| 字段名 | 类型 | 说明 |
|--------|------|------|
| pg_id | Integer | 存储对应 PG users 记录的 id |

### notes 表新增

| 字段名 | 类型 | 说明 |
|--------|------|------|
| pg_id | Integer | 存储对应 PG notes 记录的 id |

> 第一次同步后 `pg_id` 被写入，后续同步直接通过 `pg_id` 精确匹配。

---

## 五、同步流程

```
┌─────────────┐         ┌─────────────┐
│  PostgreSQL │         │    Coze     │
│  users      │  sync   │  users      │
│  notes      │ ──────→ │  notes      │
└─────────────┘         └─────────────┘

1. 拉取 PG + Coze 全量数据到内存
2. users 按 username 匹配 → 比对业务字段 → INSERT/UPDATE/DELETE
3. 构建 {pg_user_id → coze_user_id} 映射表
4. notes 按 pg_id 匹配 → 比对业务字段 → INSERT/UPDATE/DELETE
5. Coze 多余的记录（PG 中已删除）→ 物理 DELETE
```

---

## 六、应用层约束

与 Coze 一致的约束规则：

1. **username 唯一性**：注册时检查
2. **type 枚举**：仅 `1`(folder) / `2`(article)
3. **status 枚举**：仅 `1`(draft) / `2`(published)
4. **slug 唯一性**：同用户下文章 slug 唯一
5. **parent_id 合法性**：指向 `type=1` 且 `is_deleted=0` 的记录
6. **目录 status 强制**：folder 创建时 status = published
7. **软删除**：默认查询加 `is_deleted = 0`
8. **越权防护**：业务查询加 `user_id` 过滤
9. **删除目录**：递归软删除子节点
