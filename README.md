# Notes App

基于 Vue 3 + FastAPI + Coze 多维表格的个人笔记应用。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + Vite 6 + TypeScript + Naive UI + UnoCSS |
| 后端 | FastAPI + Python 3.10+ |
| 存储 | Coze 多维表格（REST API） |
| 认证 | JWT + bcrypt |
| 渲染 | marked + highlight.js + mermaid |

## 特性

- 多用户注册/登录，JWT 认证，权限隔离
- 笔记 CRUD，支持树形目录（文件夹 + 文章）
- Markdown 渲染（代码块行号/复制/折叠/行高亮、mermaid 图表）
- 全文搜索
- 草稿/发布状态、置顶、排序
- Naive UI 后台管理面板
- 响应式布局、暗色模式

## 项目结构

```
blog/
├── frontend/          # Vue 3 SPA
│   ├── src/
│   │   ├── pages/     # 6 个页面
│   │   ├── components/
│   │   ├── composables/
│   │   ├── stores/    # Pinia 状态管理
│   │   ├── api/       # Axios 请求封装
│   │   ├── router/    # Vue Router 4
│   │   └── styles/    # UnoCSS + CSS 变量
│   └── vite.config.ts
├── backend/           # FastAPI 服务
│   ├── app/
│   │   ├── api/v1/        # 路由层
│   │   ├── services/      # 业务逻辑层
│   │   ├── repositories/  # 数据访问层
│   │   ├── schemas/       # Pydantic 模型
│   │   ├── core/          # 配置/安全/Coze 客户端
│   │   └── infrastructure/coze/  # Coze 基础设施
│   ├── main.py
│   └── requirements.txt
└── vercel.json        # Vercel 部署配置
```

## 环境变量

复制 `.env.example` 为 `.env` 并填写：

```env
# Coze API
COZE_TOKEN=你的 Coze 个人访问令牌
COZE_BASE_URL=https://api.coze.cn
COZE_USERS_DATABASE_ID=users 表的数据库 ID
COZE_NOTES_DATABASE_ID=notes 表的数据库 ID

# JWT
SECRET_KEY=你的 JWT 密钥（至少 32 字符）
```

## 数据库表

在 Coze 控制台创建两张多维表格：

- `users` — 用户表（username / password_hash / is_active）
- `notes` — 笔记表（user_id / type / title / slug / content / parent_id / status / ...）

详细字段及创建步骤见 `backend/docs/coze-schema.md`。

## 开发

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器运行在 `http://localhost:3000`，API 请求自动代理到后端 `localhost:8000`。

## 部署到 Vercel

1. 将代码推送到 GitHub
2. 在 Vercel 导入项目（Monorepo，根目录为项目根）
3. 配置环境变量（见上方环境变量列表）
4. `vercel.json` 自动处理路由：`/api/v1/*` → 后端，其余 → 前端

## 文档

- [Coze 表结构设计](backend/docs/coze-schema.md)
- [Coze API 文档](backend/docs/)
- [项目架构规则](.codebuddy/rules/项目架构.mdc)
