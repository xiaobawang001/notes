"""SQLAlchemy ORM 模型（文档参考用，实际数据通过 Coze API 操作）

由于数据库是 Coze 多维表格而非 SQL，这些模型主要用于：
1. 字段定义和类型参考
2. API 文档自动生成
3. 保持与架构规则一致
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    username = Column(String(100), unique=True, nullable=False, comment="用户名（唯一）")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 密码哈希")
    email = Column(String(200), nullable=True, comment="邮箱")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="注册时间")
    is_active = Column(Integer, default=1, index=True, comment="0=禁用, 1=正常")

    # 关联
    notes = relationship("Note", back_populates="user")


class Note(Base):
    """笔记模型"""
    __tablename__ = "notes"

    # ── 规则必选字段 ──
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False, comment="所属用户")
    title = Column(String(500), nullable=False, comment="标题")
    content = Column(Text, nullable=True, comment="Markdown 正文")
    ai_summary = Column(Text, nullable=True, comment="AI 生成摘要")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # ── 树形层级扩展 ──
    type = Column(Integer, default=2, index=True, comment="1=folder, 2=article")
    slug = Column(String(200), nullable=True, comment="URL 标识")
    parent_id = Column(Integer, default=0, index=True, comment="父级 ID, 0=顶级")
    status = Column(Integer, default=1, index=True, comment="1=draft, 2=published")
    pinned = Column(Integer, default=0, index=True, comment="0=否, 1=是")
    sort_order = Column(Integer, default=0, comment="排序权重")
    word_count = Column(Integer, default=0, comment="字数")
    is_deleted = Column(Integer, default=0, index=True, comment="0=正常, 1=已删除")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    # 关联
    user = relationship("User", back_populates="notes")
