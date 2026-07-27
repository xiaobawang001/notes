"""SQLAlchemy ORM 模型（PostgreSQL 表结构定义 + 文档参考）

PG 表为主数据源，Coze 作为同步副本。Coze 侧通过 `pg_id` 字段
存储 PG 记录 ID，实现跨平台精确匹配。

Coze 平台自有字段（id, sys_platform, uuid, bstudio_create_time）不在此定义。"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """用户模型（PG 主表，id 对应 Coze pg_id）"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键（BIGINT，自增，对应 Coze pg_id）")
    username = Column(String(100), unique=True, nullable=False, comment="用户名（唯一）")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 密码哈希")
    email = Column(String(200), nullable=True, comment="邮箱")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="注册时间")
    is_active = Column(Integer, default=1, index=True, comment="0=禁用, 1=正常")
    role = Column(String(20), default="user", comment="user=普通用户, admin=管理员")

    notes = relationship("Note", back_populates="user")


class Note(Base):
    """笔记模型（PG 主表，id 对应 Coze pg_id）"""
    __tablename__ = "notes"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键（BIGINT，自增，对应 Coze pg_id）")
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="所属用户")
    title = Column(String(500), nullable=False, comment="标题")
    content = Column(Text, nullable=True, comment="Markdown 正文")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    type = Column(Integer, default=2, index=True, comment="1=folder, 2=article")
    slug = Column(String(200), nullable=True, comment="URL 标识")
    parent_id = Column(BigInteger, default=0, index=True, comment="父级 ID（BIGINT）, 0=顶级")
    status = Column(Integer, default=1, index=True, comment="1=draft, 2=published")
    pinned = Column(Integer, default=0, index=True, comment="0=否, 1=是")
    sort_order = Column(Integer, default=0, comment="排序权重")
    word_count = Column(Integer, default=0, comment="字数")
    is_deleted = Column(Integer, default=0, index=True, comment="0=正常, 1=已删除")
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间")

    user = relationship("User", back_populates="notes")
