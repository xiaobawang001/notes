"""笔记相关 Pydantic Schema"""
from typing import Optional
from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """创建笔记请求"""
    type: str = Field(default="article", pattern="^(folder|article)$", description="类型：folder / article")
    title: str = Field(..., min_length=1, max_length=500, description="标题（必填）")
    slug: Optional[str] = Field(default=None, max_length=200, description="URL 标识")
    content: Optional[str] = Field(default=None, description="Markdown 正文")
    ai_summary: Optional[str] = Field(default=None, description="AI 摘要")
    parent_id: int = Field(default=0, description="父级笔记 ID，0=顶级")
    status: str = Field(default="published", pattern="^(draft|published)$", description="状态")
    pinned: bool = Field(default=False, description="是否置顶")
    sort_order: int = Field(default=0, description="排序权重")


class NoteUpdate(BaseModel):
    """更新笔记请求（所有字段可选，只更新传入的）"""
    type: Optional[str] = Field(default=None, pattern="^(folder|article)$")
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    slug: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = None
    ai_summary: Optional[str] = None
    parent_id: Optional[int] = None
    status: Optional[str] = Field(default=None, pattern="^(draft|published)$")
    pinned: Optional[bool] = None
    sort_order: Optional[int] = None


class NoteItem(BaseModel):
    """笔记单条响应"""
    id: int
    user_id: int = 0
    type: str = "article"
    title: str = ""
    slug: str = ""
    content: str = ""
    ai_summary: str = ""
    parent_id: int = 0
    status: str = "draft"
    pinned: bool = False
    sort_order: int = 0
    word_count: int = 0
    created_at: str = ""
    updated_at: str = ""


class NoteListParams(BaseModel):
    """笔记列表查询参数"""
    type: Optional[str] = Field(default=None, pattern="^(folder|article)$")
    status: Optional[str] = Field(default=None, pattern="^(draft|published)$")
    parent_id: Optional[int] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=500)


class CategoryTreeItem(BaseModel):
    """目录树节点"""
    id: int
    type: str
    name: str = Field(..., alias="title")
    slug: str = ""
    parent_id: int = 0
    children: list["CategoryTreeItem"] = Field(default_factory=list)

    class Config:
        populate_by_name = True
