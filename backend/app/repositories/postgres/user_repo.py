"""用户数据访问层（PostgreSQL）：使用 SQLAlchemy async 操作 users 表"""
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.database import get_db


class PostgresUserRepo:
    """用户 Repository（PostgreSQL）：处理 users 表的 CRUD"""

    # ── 模型 → 字典转换（与 Coze coze_to_user 返回格式一致）──
    @staticmethod
    def _to_dict(user: User | None) -> dict | None:
        if user is None:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "password_hash": user.password_hash,
            "email": user.email or "",
            "created_at": user.created_at.isoformat() if user.created_at else "",
            "is_active": bool(user.is_active),
            "role": user.role or "user",
        }

    async def find_by_username(self, username: str) -> dict | None:
        """按用户名查询用户"""
        async with get_db() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return self._to_dict(result.scalar_one_or_none())

    async def find_by_id(self, user_id: int) -> dict | None:
        """按 ID 查询用户"""
        async with get_db() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return self._to_dict(result.scalar_one_or_none())

    async def create(
        self, username: str, password_hash: str, email: str | None = None, role: str = "user"
    ) -> dict | None:
        """创建新用户，返回创建后的用户信息"""
        async with get_db() as session:
            user = User(
                username=username,
                password_hash=password_hash,
                email=email,
                role=role,
                is_active=1,
                created_at=datetime.utcnow(),
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return self._to_dict(user)

    async def count(self) -> int:
        """统计用户总数"""
        async with get_db() as session:
            result = await session.execute(select(func.count(User.id)))
            return result.scalar() or 0

    async def find_all(self) -> list[dict]:
        """查询全部用户（sync 用）"""
        async with get_db() as session:
            result = await session.execute(select(User))
            return [self._to_dict(u) for u in result.scalars().all()]
