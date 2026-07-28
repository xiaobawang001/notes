"""认证服务：注册、登录、Token 验证

⚠️ 始终使用 PostgreSQL 存储用户数据，不受后端切换影响。
Coze 仅用于业务数据（笔记），不存储用户凭证。"""
from app.repositories.postgres.user_repo import PostgresUserRepo
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


class AuthService:
    """认证服务——固定使用 PostgreSQL，不跟随后端切换"""

    def __init__(self, user_repo=None):
        self.user_repo = user_repo if user_repo is not None else PostgresUserRepo()

    async def register(self, req: RegisterRequest) -> TokenResponse:
        """用户注册：检查用户名唯一 → bcrypt 哈希密码 → 创建用户（默认 user 角色）→ 返回 Token"""
        # 检查用户名唯一性
        existing = await self.user_repo.find_by_username(req.username)
        if existing:
            raise ValueError("用户名已存在")

        # 所有注册用户默认 role=user，管理员由运维在 Coze 表中手动指定
        hashed = hash_password(req.password)
        user = await self.user_repo.create(req.username, hashed, req.email, role="user")
        if not user:
            raise RuntimeError("注册失败，请重试")

        # 返回 Token（含 role）
        return TokenResponse(
            token=create_access_token(user["id"], user["username"], user.get("role", "user")),
            user_id=user["id"],
            username=user["username"],
            role=user.get("role", "user"),
        )

    async def login(self, req: LoginRequest) -> TokenResponse:
        """用户登录：验密 → 返回 JWT Token（含 role）"""
        user = await self.user_repo.find_by_username(req.username)
        if not user:
            raise ValueError("用户名或密码错误")
        if not user.get("is_active"):
            raise ValueError("账户已被禁用")

        if not verify_password(req.password, user["password_hash"]):
            raise ValueError("用户名或密码错误")

        return TokenResponse(
            token=create_access_token(user["id"], user["username"], user.get("role", "user")),
            user_id=user["id"],
            username=user["username"],
            role=user.get("role", "user"),
        )

    async def refresh_token(self, token: str) -> TokenResponse:
        """刷新 Token：验证旧 Token → 签发新 Token（含 role）"""
        from app.core.security import verify_access_token
        payload = verify_access_token(token)
        if not payload:
            raise ValueError("Token 无效或已过期")

        user_id = payload.get("sub")
        username = payload.get("username", "")
        role = payload.get("role", "user")

        user = None
        if user_id is not None:
            try:
                uid = int(user_id)
                user = await self.user_repo.find_by_id(uid)
            except (TypeError, ValueError):
                user = None

        if user is None and username:
            user = await self.user_repo.find_by_username(username)

        if not user:
            raise ValueError("用户不存在")

        return TokenResponse(
            token=create_access_token(user["id"], user["username"], user.get("role", role)),
            user_id=user["id"],
            username=user["username"],
            role=user.get("role", role),
        )
