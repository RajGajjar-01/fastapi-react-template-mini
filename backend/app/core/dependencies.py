from collections.abc import AsyncGenerator
from typing import cast

from fastapi import Depends, HTTPException, Request, status
from httpx import AsyncClient
from jwt import PyJWTError

from app.core.security import verify_token
from app.models.user import UserProfile
from app.repositories.user_repository import UserRepository


async def get_current_user(request: Request) -> dict[str, str | object]:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "NOT_AUTHENTICATED", "detail": "Not authenticated", "type": "about:blank", "status": 401},
        )
    try:
        return verify_token(token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "TOKEN_EXPIRED", "detail": "Invalid or expired token", "type": "about:blank", "status": 401},
        )


async def get_user_repository(request: Request) -> AsyncGenerator[UserRepository]:
    pool = request.app.state.pool
    yield UserRepository(pool)


async def get_supabase_client(request: Request) -> AsyncClient:
    return cast(AsyncClient, request.app.state.supabase_client)


async def get_current_profile(
    current_user: dict[str, str | object] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserProfile:
    profile = await user_repo.get_by_id(cast(str, current_user["sub"]))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"title": "PROFILE_NOT_FOUND", "detail": "Profile not found", "type": "about:blank", "status": 404},
        )
    return profile


async def get_current_role(
    current_user: dict[str, str | object] = Depends(get_current_user),
) -> str:
    app_metadata = cast(dict[str, object], current_user.get("app_metadata") or {})
    return cast(str, app_metadata.get("user_role", "user"))


async def require_admin(
    role: str = Depends(get_current_role),
) -> str:
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"title": "FORBIDDEN", "detail": "Admin access required", "type": "about:blank", "status": 403},
        )
    return role


async def require_moderator_or_admin(
    role: str = Depends(get_current_role),
) -> str:
    if role not in ("moderator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"title": "FORBIDDEN", "detail": "Moderator or admin access required", "type": "about:blank", "status": 403},
        )
    return role
