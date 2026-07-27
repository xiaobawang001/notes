# Blog Nuxt

基于 Nuxt 3 + Coze Database 的动态笔记网站。

## 特性

- 笔记增删改查，数据存储在 Coze Database
- 左侧目录树，右侧文章内容（类似文档站/笔记软件）
- Markdown 在线编辑器（编辑 / 预览 / 分屏）
- 多级目录层级、标签、置顶、草稿/发布状态
- 全文搜索
- 响应式布局

## 环境变量

复制 `.env.example` 为 `.env` 并填写：

```env
COZE_TOKEN=你的 Coze 个人访问令牌
COZE_BASE_URL=https://api.coze.cn
COZE_DATABASE_ID=文章表的数据库 ID
```

## 数据库表结构

只需要一张 `articles` 表，参考 `coze-schema.md` 在 Coze 中创建。

层级关系通过 `path` 字段体现，例如 `服务器运维/docker`，无需单独的分类表。

## 开发

```bash
npm install
npm run dev
```

## 迁移旧文档

先启动开发服务器，然后执行：

```bash
npm run migrate
```

脚本会读取 `blog-archive/docs` 下的 Markdown 文件，根据原目录结构生成 `path` 字段，通过本地 API 写入 Coze。

## 部署到 Vercel

1. 将代码推送到 GitHub
2. 在 Vercel 导入项目
3. 配置环境变量（与 `.env.example` 一致）
4. 自动部署完成

## 归档

原 VitePress 静态版本已完整备份到 `blog-archive/` 目录。
