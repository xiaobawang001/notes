"""认证服务：注册、登录、Token 验证"""
from app.repositories.user_repo import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def register(self, req: RegisterRequest) -> TokenResponse:
        """用户注册：检查用户名唯一 → bcrypt 哈希密码 → 创建用户 → 返回 Token"""
        # 检查用户名唯一性
        existing = await self.user_repo.find_by_username(req.username)
        if existing:
            raise ValueError("用户名已存在")

        # 创建用户
        hashed = hash_password(req.password)
        user = await self.user_repo.create(req.username, hashed, req.email)
        if not user:
            raise RuntimeError("注册失败，请重试")

        # 返回 Token
        return TokenResponse(
            token=create_access_token(user["id"], user["username"]),
            user_id=user["id"],
            username=user["username"],
        )

    async def login(self, req: LoginRequest) -> TokenResponse:
        """用户登录：验密 → 返回 JWT Token"""
        user = await self.user_repo.find_by_username(req.username)
        if not user:
            raise ValueError("用户名或密码错误")
        if not user.get("is_active"):
            raise ValueError("账户已被禁用")

        if not verify_password(req.password, user["password_hash"]):
            raise ValueError("用户名或密码错误")

        return TokenResponse(
            token=create_access_token(user["id"], user["username"]),
            user_id=user["id"],
            username=user["username"],
        )

    async def refresh_token(self, token: str) -> TokenResponse:
        """刷新 Token：验证旧 Token → 签发新 Token"""
        from app.core.security import verify_access_token
        payload = verify_access_token(token)
        if not payload:
            raise ValueError("Token 无效或已过期")

        user_id = int(payload.get("sub", 0))
        username = payload.get("username", "")
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        return TokenResponse(
            token=create_access_token(user["id"], user["username"]),
            user_id=user["id"],
            username=user["username"],
        )
