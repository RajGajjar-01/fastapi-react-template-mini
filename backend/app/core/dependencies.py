from collections.abc import AsyncGenerator
from typing import cast

from fastapi import Depends, HTTPException, Request, status
from httpx import AsyncClient
from jwt import PyJWTError

from app.core.config import settings
from app.core.security import verify_token_async
from app.models.user import UserProfile
from app.repositories.user_repository import UserRepository


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"title": "FORBIDDEN", "detail": detail, "type": "about:blank", "status": 403},
    )


async def get_current_user(request: Request) -> dict[str, str | object]:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "NOT_AUTHENTICATED", "detail": "Not authenticated", "type": "about:blank", "status": 401},
        )
    try:
        return await verify_token_async(token)
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


async def require_trusted_origin(request: Request) -> None:
    """Reject cross-site browser requests to cookie-authenticated routes that
    have no JSON body (logout, refresh). Such requests can be sent without a
    CORS preflight, so the allowlist is checked directly."""
    origin = request.headers.get("origin")
    if origin is None:
        return
    own_origin = f"{request.url.scheme}://{request.url.netloc}"
    if origin != own_origin and origin not in settings.ALLOWED_ORIGINS:
        raise _forbidden("Origin not allowed")


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


async def _current_db_role(
    current_user: dict[str, str | object],
    user_repo: UserRepository,
) -> str:
    profile = await user_repo.get_by_id(cast(str, current_user["sub"]))
    return profile.role if profile is not None else "user"


async def require_admin(
    role: str = Depends(get_current_role),
    current_user: dict[str, str | object] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> str:
    # The token claim is only a hint that can be up to one token lifetime old.
    # The stored role must agree, so a demotion applies at once.
    if role != "admin" or await _current_db_role(current_user, user_repo) != "admin":
        raise _forbidden("Admin access required")
    return role


async def require_moderator_or_admin(
    role: str = Depends(get_current_role),
    current_user: dict[str, str | object] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> str:
    if role not in ("moderator", "admin"):
        raise _forbidden("Moderator or admin access required")
    if await _current_db_role(current_user, user_repo) not in ("moderator", "admin"):
        raise _forbidden("Moderator or admin access required")
    return role
