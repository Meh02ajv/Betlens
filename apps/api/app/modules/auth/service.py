from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_reset_token,
    generate_verification_token,
    hash_password,
    verify_password,
)
from app.db.models import PasswordResetToken, User
from app.modules.auth.schemas import (
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
)


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def signup(self, data: SignupRequest) -> tuple[User, str]:
        """Create a new user. Returns (user, verification_token)."""
        existing = await self.db.scalar(select(User).where(User.email == data.email))
        if existing:
            raise AuthError("Email already registered", 409)

        if not data.is_adult_confirmed:
            raise AuthError("You must confirm you are 18 or older to register", 400)

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            name=data.name,
            is_adult_confirmed=True,
        )
        self.db.add(user)
        await self.db.flush()

        token = generate_verification_token()
        # In production, store token hash and send email
        # For dev, we return the token directly
        return user, token

    async def verify_email(self, token: str) -> User:
        """Mark email as verified."""
        # In production, look up token hash in DB
        # For dev mock: accept any token and verify the most recent unverified user
        result = await self.db.execute(
            select(User).where(User.email_verified_at.is_(None)).order_by(User.created_at.desc())
        )
        user = result.scalars().first()
        if not user:
            raise AuthError("Invalid or expired verification token", 400)
        user.email_verified_at = datetime.now(UTC)
        await self.db.flush()
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.db.scalar(select(User).where(User.email == data.email))
        if not user or not user.password_hash:
            raise AuthError("Invalid email or password", 401)
        if not verify_password(data.password, user.password_hash):
            raise AuthError("Invalid email or password", 401)
        if user.deleted_at:
            raise AuthError("Account has been deleted", 403)

        return TokenResponse(
            access_token=create_access_token(str(user.id), {"role": user.role, "plan": user.plan}),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Wrong token type")
            user_id = UUID(payload["sub"])
        except (ValueError, KeyError) as exc:
            raise AuthError("Invalid refresh token", 401) from exc

        user = await self.db.get(User, user_id)
        if not user or user.deleted_at:
            raise AuthError("User not found", 401)

        return TokenResponse(
            access_token=create_access_token(str(user.id), {"role": user.role, "plan": user.plan}),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def forgot_password(self, email: str) -> str | None:
        """Returns reset token (for dev). In production, sends email."""
        user = await self.db.scalar(select(User).where(User.email == email))
        if not user:
            return None  # Don't reveal whether email exists

        token = generate_reset_token()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(UTC) + timedelta(minutes=30)

        reset = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(reset)
        await self.db.flush()
        return token

    async def reset_password(self, data: ResetPasswordRequest) -> None:
        token_hash = hashlib.sha256(data.token.encode()).hexdigest()
        reset = await self.db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.now(UTC),
            )
        )
        if not reset:
            raise AuthError("Invalid or expired reset token", 400)

        user = await self.db.get(User, reset.user_id)
        if not user:
            raise AuthError("User not found", 404)

        user.password_hash = hash_password(data.new_password)
        reset.used_at = datetime.now(UTC)
        await self.db.flush()