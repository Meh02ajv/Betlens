from fastapi import APIRouter, HTTPException

from app.core.deps import DbSession
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.modules.auth.service import AuthError, AuthService

router = APIRouter()


def _svc(db: DbSession) -> AuthService:
    return AuthService(db)


@router.post("/signup", response_model=MessageResponse, status_code=201)
async def signup(data: SignupRequest, db: DbSession) -> MessageResponse:
    try:
        user, token = await _svc(db).signup(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    # In production, send verification email here
    return MessageResponse(message="Account created. Please check your email to verify your account.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: VerifyEmailRequest, db: DbSession) -> MessageResponse:
    try:
        await _svc(db).verify_email(data.token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return MessageResponse(message="Email verified successfully.")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    try:
        return await _svc(db).login(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: DbSession) -> TokenResponse:
    try:
        return await _svc(db).refresh(data.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout() -> MessageResponse:
    # Stateless JWT: client discards tokens. In production, add token to blocklist.
    return MessageResponse(message="Logged out successfully.")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: DbSession) -> MessageResponse:
    await _svc(db).forgot_password(data.email)
    # Always return success to avoid email enumeration
    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: DbSession) -> MessageResponse:
    try:
        await _svc(db).reset_password(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return MessageResponse(message="Password reset successfully.")