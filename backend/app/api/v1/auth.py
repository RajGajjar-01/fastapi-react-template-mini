import logging
from typing import cast

from fastapi import APIRouter, Depends, Request, Response, status
from httpx import AsyncClient

from app.core.config import settings
from app.core.dependencies import get_current_user, get_user_repository
from app.core.security import verify_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    UpdateProfileRequest,
)
from app.schemas.common import err

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


def set_auth_cookies(response: Response, tokens: dict[str, str]) -> None:
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=3600,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=2592000,
    )


def delete_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", httponly=True, secure=settings.COOKIE_SECURE, samesite="lax")
    response.delete_cookie("refresh_token", httponly=True, secure=settings.COOKIE_SECURE, samesite="lax")


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, object]:
    async with AsyncClient() as client:
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
        raise err("INVALID_CREDENTIALS", "Invalid email or password")

    tokens = supabase_resp.json()
    payload = verify_token(tokens["access_token"])

    await user_repo.upsert(
        user_id=cast(str, payload["sub"]),
        email=cast(str, payload["email"]),
    )

    set_auth_cookies(response, tokens)

    return {"data": {"message": "Logged in", "email": body.email}}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    body: SignupRequest,
    response: Response,
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, object]:
    async with AsyncClient() as client:
        supabase_resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/signup",
            headers={
                "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
                "Content-Type": "application/json",
            },
            json={"email": body.email, "password": body.password},
        )

    if supabase_resp.status_code != 200:
        detail = supabase_resp.json().get("msg", "Signup failed")
        raise err("SIGNUP_FAILED", detail)

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

    return {
        "data": {
            "message": "Signed up" if auto_confirmed else "Confirmation email sent",
            "email": body.email,
        }
    }


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
) -> dict[str, object]:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise err("NOT_AUTHENTICATED", "Not authenticated", status_code=401)

    async with AsyncClient() as client:
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
        raise err("SESSION_EXPIRED", "Session expired, please log in again", status_code=401)

    tokens = supabase_resp.json()

    set_auth_cookies(response, tokens)

    return {"data": {"message": "Refreshed"}}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
) -> None:
    access_token = request.cookies.get("access_token")

    if access_token:
        async with AsyncClient() as client:
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
) -> dict[str, object]:
    user_id = cast(str, current_user["sub"])
    profile = await user_repo.get_by_id(user_id)
    if profile is None:
        raise err("PROFILE_NOT_FOUND", "Profile not found", status_code=404)
    return {
        "data": {
            "user_id": profile.id,
            "email": profile.email,
            "full_name": profile.full_name,
            "avatar_url": profile.avatar_url,
        }
    }


@router.patch("/me")
async def update_me(
    body: UpdateProfileRequest,
    current_user: dict[str, str | object] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, object]:
    user_id = cast(str, current_user["sub"])
    profile = await user_repo.update_profile(
        user_id,
        full_name=body.full_name,
        avatar_url=body.avatar_url,
    )
    if profile is None:
        raise err("PROFILE_NOT_FOUND", "Profile not found", status_code=404)
    return {
        "data": {
            "user_id": profile.id,
            "email": profile.email,
            "full_name": profile.full_name,
            "avatar_url": profile.avatar_url,
        }
    }
