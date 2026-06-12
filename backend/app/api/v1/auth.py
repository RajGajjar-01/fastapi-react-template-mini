import logging
from typing import Literal, cast

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from httpx import AsyncClient

from app.core.config import settings
from app.core.dependencies import (
    get_current_user,
    get_supabase_client,
    get_user_repository,
)
from app.core.response import error_response, success_response
from app.core.security import verify_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    UpdateProfileRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


def _samesite() -> Literal["lax", "none"]:
    return "none" if settings.COOKIE_SECURE else "lax"


def set_auth_cookies(response: Response, tokens: dict[str, str]) -> None:
    samesite = _samesite()
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=samesite,
        max_age=3600,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=samesite,
        max_age=2592000,
    )


def delete_auth_cookies(response: Response) -> None:
    samesite = _samesite()
    response.delete_cookie("access_token", httponly=True, secure=settings.COOKIE_SECURE, samesite=samesite)
    response.delete_cookie("refresh_token", httponly=True, secure=settings.COOKIE_SECURE, samesite=samesite)


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    client: AsyncClient = Depends(get_supabase_client),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    supabase_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "password"},
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
        },
        json={"email": body.email, "password": body.password},
    )

    if supabase_resp.status_code != 200:
        return error_response(401, "INVALID_CREDENTIALS", "Invalid email or password")

    tokens = supabase_resp.json()
    payload = verify_token(tokens["access_token"])

    await user_repo.upsert(
        user_id=cast(str, payload["sub"]),
        email=cast(str, payload["email"]),
    )

    set_auth_cookies(response, tokens)

    return success_response({"message": "Logged in", "email": body.email})


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    body: SignupRequest,
    response: Response,
    client: AsyncClient = Depends(get_supabase_client),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    supabase_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/signup",
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
        },
        json={"email": body.email, "password": body.password},
    )

    if supabase_resp.status_code != 200:
        err_body = supabase_resp.json()
        logger.warning("Supabase signup failed (%s): %s", supabase_resp.status_code, err_body)
        detail = err_body.get("msg") or err_body.get("error_description") or err_body.get("message") or "Signup failed"
        return error_response(400, "SIGNUP_FAILED", detail)

    data = supabase_resp.json()
    auto_confirmed = bool(data.get("access_token"))

    if auto_confirmed:
        try:
            payload = verify_token(data["access_token"])
            await user_repo.upsert(
                user_id=cast(str, payload["sub"]),
                email=cast(str, payload["email"]),
                full_name=body.full_name,
            )
            set_auth_cookies(response, data)
        except Exception:
            logger.warning("Signup token verification failed", exc_info=True)

    return success_response(
        {"message": "Signed up" if auto_confirmed else "Confirmation email sent", "email": body.email},
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    client: AsyncClient = Depends(get_supabase_client),
) -> JSONResponse:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return error_response(401, "NOT_AUTHENTICATED", "Not authenticated")

    supabase_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "refresh_token"},
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
        },
        json={"refresh_token": refresh_token},
    )

    if supabase_resp.status_code != 200:
        return error_response(401, "SESSION_EXPIRED", "Session expired, please log in again")

    tokens = supabase_resp.json()

    set_auth_cookies(response, tokens)

    return success_response({"message": "Refreshed"})


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    client: AsyncClient = Depends(get_supabase_client),
) -> None:
    access_token = request.cookies.get("access_token")

    if access_token:
        await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/logout",
            headers={
                "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
                "Authorization": f"Bearer {access_token}",
            },
        )

    delete_auth_cookies(response)


@router.get("/me")
async def get_me(
    current_user: dict[str, str | object] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    user_id = cast(str, current_user["sub"])
    profile = await user_repo.get_by_id(user_id)
    if profile is None:
        return error_response(404, "PROFILE_NOT_FOUND", "Profile not found")
    return success_response({
        "user_id": profile.id,
        "email": profile.email,
        "full_name": profile.full_name,
        "avatar_url": profile.avatar_url,
    })


@router.patch("/me")
async def update_me(
    body: UpdateProfileRequest,
    current_user: dict[str, str | object] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    user_id = cast(str, current_user["sub"])
    profile = await user_repo.update_profile(
        user_id,
        full_name=body.full_name,
        avatar_url=body.avatar_url,
    )
    if profile is None:
        return error_response(404, "PROFILE_NOT_FOUND", "Profile not found")
    return success_response({
        "user_id": profile.id,
        "email": profile.email,
        "full_name": profile.full_name,
        "avatar_url": profile.avatar_url,
    })


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    client: AsyncClient = Depends(get_supabase_client),
) -> JSONResponse:
    resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/recover",
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
        },
        json={"email": body.email},
    )

    if resp.status_code != 200:
        return error_response(400, "RESET_FAILED", "Failed to send reset email")

    return success_response({"message": "If the email exists, a reset link has been sent"})


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    client: AsyncClient = Depends(get_supabase_client),
) -> JSONResponse:
    token_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "recovery"},
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
        },
        json={"token": body.token},
    )

    if token_resp.status_code != 200:
        return error_response(400, "INVALID_TOKEN", "Invalid or expired reset token")

    session = token_resp.json()
    access_token = session["access_token"]

    update_resp = await client.put(
        f"{settings.SUPABASE_URL}/auth/v1/user",
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"password": body.password},
    )

    if update_resp.status_code != 200:
        return error_response(400, "PASSWORD_UPDATE_FAILED", "Failed to update password")

    return success_response({"message": "Password updated successfully"})
