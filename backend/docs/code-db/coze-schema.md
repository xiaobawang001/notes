# Coze 数据库表结构设计

> Coze 可用字段类型仅支持：`String`、`Integer`、`Time`、`Number`、`Boolean`。本文档已按此映射。

## articles（文章/目录表）

这张表同时存储**目录(folder)** 和 **文章(article)** 两种记录，通过 `type` 字段区分，通过 `parent_id` 自关联组织层级。

### Coze 自带默认字段

以下字段由 Coze 平台自动生成和维护，建表时无需手动创建，写入时也无需应用层传值：

| 字段名                | 描述                          | 设为索引 | 数据类型 | 是否必要 |
|-----------------------|-------------------------------|---------|---------|---------|
| id                    | 数据的唯一标识（主键）          | -       | Integer | 是      |
| sys_platform          | 数据产生或使用的渠道            | -       | String  | 是      |
| uuid                  | 用户唯一标识，由系统生成        | -       | String  | 是      |
| bstudio_create_time   | 数据插入的时间                 | -       | Time    | 是      |

> 主键是 `id`（Integer），**不是** `record_id`。此前代码中按 `record_id` 过滤更新/删除会报 `Unknown column 'record_id'` 错误，应统一改为按 `id` 过滤。

### 业务字段

| 字段名       | Coze 字段类型 | 设为索引 | 是否必填 | 默认值  | 说明                                    |
|-------------|--------------|---------|---------|--------|----------------------------------------|
| type        | Integer      | 是      | 是      | 2      | 枚举：`1=folder` / `2=article`（见下方映射表） |
| title       | String       | 否      | 是      | -      | 标题（文章标题或目录名称）               |
| slug        | String       | 否      | 否      | -      | URL 标识，文章必填，目录可空             |
| content     | String       | 否      | 否      | -      | Markdown 正文，仅文章有效                |
| summary     | String       | 否      | 否      | -      | 文章摘要                                |
| parent_id   | Integer      | 是      | 否      | -      | 父级记录 `id`，顶级为空（见下方类型说明） |
| status      | Integer      | 是      | 是      | 1      | 枚举：`1=draft` / `2=published`（见下方映射表） |
| pinned      | Integer      | 是      | 是      | 0      | 是否置顶：`0=false` / `1=true`           |
| sort_order  | Integer      | 否      | 否      | 0      | 同级排序权重，数字越小越靠前              |
| word_count  | Integer      | 否      | 否      | 0      | 字数统计                                |
| is_deleted  | Integer      | 是      | 是      | 0      | 软删除标记：`0=正常` / `1=已删除`（见下方说明）|
| deleted_at  | Time         | 否      | 否      | -      | 软删除时间戳，仅作记录用途，不参与查询过滤 |
| created_at  | Time         | 否      | 是      | -      | 创建时间，ISO 8601 格式                  |
| updated_at  | Time         | 否      | 是      | -      | 更新时间，ISO 8601 格式                  |

> **类型调整说明**：`type`、`status`、`pinned`、`parent_id`、`is_deleted` 原本设计为 String/Boolean，现改为 **Integer 编码**，是因为 Coze 只允许 Integer 类型设索引。这几个字段恰好是目录树构建、列表筛选、软删除过滤里最高频的查询条件，改成 Integer 后即可设索引，避免全表扫描。`slug`/`title`/`content`/`summary` 属于自由文本，无法枚举化，仍保留 String，且依然不可设索引。

#### 枚举映射表

| 字段 | 值 | 含义 |
|---|---|---|
| `type` | `1` | folder（目录） |
| `type` | `2` | article（文章） |
| `status` | `1` | draft（草稿） |
| `status` | `2` | published（已发布） |
| `pinned` | `0` | 未置顶 |
| `pinned` | `1` | 已置顶 |
| `is_deleted` | `0` | 正常 |
| `is_deleted` | `1` | 已软删除 |

### type 字段说明

- **`1`（folder）**：目录/文件夹，只填写 `title`，`content` 和 `slug` 可为空
- **`2`（article）**：文章，必须填写 `title` 和 `slug`，`parent_id` 指向所属目录

### parent_id 字段说明

`parent_id` 存储父级记录的 `id`，用于构建树形目录结构。

> **类型说明**：`parent_id` 已改为 Integer，与主键 `id` 类型一致，写入/比较时直接使用数值，无需再做字符串格式对齐。顶级记录 `parent_id` 留空（NULL）。

示例数据：

| id      | type | title      | slug           | parent_id | status |
|---------|------|-----------|----------------|-----------|--------|
| 1001    | 1    | 服务器运维  |                |           | 2      |
| 1002    | 1    | docker     |                | 1001      | 2      |
| 1003    | 2    | Docker安装 | docker-install | 1002      | 2      |

对应目录树：

```
服务器运维
  └── docker
        └── Docker安装
```

### status 字段说明

- 文章状态：`2`(published，前台可见) / `1`(draft，仅后台可见)
- 目录状态：固定为 `2`(published)，否则其下文章会在目录树中"失踪"

### sort_order 字段说明

控制同级目录/文章的显示顺序。例如：
- 目录 `docker` 的 `sort_order = 0`
- 目录 `psql` 的 `sort_order = 1`
- 则 `docker` 排在 `psql` 前面

### 时间字段说明

`created_at` 和 `updated_at` 使用 ISO 8601 字符串格式：

```
2026-07-21T12:00:00.000Z
```

### 接口值类型说明

Coze API 要求插入、更新时字段值以**字符串**形式传输，即使字段类型是 Integer/Boolean/Time 也不例外：

- Integer（含 `type`/`status`/`pinned`/`parent_id`/`is_deleted`/`sort_order`/`word_count`）：`"0"`、`"1"`、`"123"`
- Time：`"2026-07-21T12:00:00.000Z"`

应用层在调用 Coze API 前统一做 `String(value)` 转换。

### pinned 字段说明（置顶）

`pinned` 为 `1` 时，该文章会被置顶展示。

**置顶规则**：

1. **首页默认文章**：优先取 `pinned = 1` 且已发布的文章
2. **左侧目录树**：在同级节点排序时，置顶文章排在最前面
3. **管理后台列表**：置顶文章显示在最前面

**排序优先级**：

```
pinned = 1 优先
  → sort_order 越小越靠前
    → updated_at 越新越靠前
```

例如同一目录下有两篇文章：

| title | pinned | sort_order | 显示顺序 |
|-------|--------|------------|---------|
| 常用命令 | 1 | 0 | 第 1 |
| 安装指南 | 0 | 0 | 第 2 |
| 高级配置 | 0 | 1 | 第 3 |

### 说明

- `slug` 字段用于文章详情页路由，建议对文章设置唯一约束。
- `word_count` 由应用层根据 `content` 长度自动计算。

### is_deleted / deleted_at 字段说明（软删除）

- 删除文章/目录时，应用层将 `is_deleted` 置为 `1`、`deleted_at` 写入当前时间戳，不做物理删除，避免误删无法恢复。
- 所有查询（目录树、列表、搜索、详情）都必须附加 `is_deleted = 0` 的过滤条件，否则已删除记录会重新出现。`is_deleted` 是 Integer 类型，可设索引，作为软删除的主要过滤字段；`deleted_at` 仅作时间记录，不参与过滤。
- 如需彻底清理，可由后台定期任务对 `deleted_at` 超过一定时限（且 `is_deleted = 1`）的记录做真正的物理删除。

## 应用层需要保证的约束

Coze 文档型数据库通常不支持外键和复杂约束，以下逻辑需在代码中处理：

1. **枚举校验**：`type` 只能是 `1`(folder) / `2`(article)，`status` 只能是 `1`(draft) / `2`(published)
2. **slug 唯一性**：在文章范围内唯一，应用层写入前检查
3. **parent_id 合法性**：必须指向一个 `type = 1`(folder) 且 `is_deleted = 0` 的记录
4. **目录状态**：创建/修改目录时 `status` 强制为 `2`(published)
5. **删除目录前**：检查是否存在未删除的子目录或子文章，避免孤立数据
6. **软删除过滤**：所有查询默认加 `is_deleted = 0` 条件

## 主要查询场景

| 功能           | 查询条件                                                               |
|---------------|------------------------------------------------------------------------|
| 构建左侧目录树  | `is_deleted = 0` AND（`status = 2` 的 `type = 1` + `status = 2` 的 `type = 2`），按 `parent_id` 分组递归 |
| 首页默认文章    | `type = 2` AND `status = 2` AND `is_deleted = 0`                        |
| 文章详情        | `slug = ?` AND `is_deleted = 0`                                        |
| 管理后台列表    | 可筛选 `type` 和 `status`，默认加 `is_deleted = 0`                       |
| 全文搜索        | `type = 2` AND `status = 2` AND `is_deleted = 0` AND 标题/正文/摘要包含关键词 |

## 环境变量

在 Vercel / 本地 `.env` 中配置：

```env
COZE_TOKEN=你的 Coze 个人访问令牌
COZE_BASE_URL=https://api.coze.cn
COZE_DATABASE_ID=articles 表的数据库 ID
```
