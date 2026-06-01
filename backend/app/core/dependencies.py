from collections.abc import AsyncGenerator
from typing import cast

from fastapi import HTTPException, Request, status
from httpx import AsyncClient
from jwt import PyJWTError

from app.core.security import verify_token
from app.repositories.user_repository import UserRepository


async def get_current_user(request: Request) -> dict[str, str | object]:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NOT_AUTHENTICATED", "message": "Not authenticated"},
        )
    try:
        return verify_token(token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Invalid or expired token"},
        )


async def get_user_repository(request: Request) -> AsyncGenerator[UserRepository]:
    pool = request.app.state.pool
    yield UserRepository(pool)


async def get_supabase_client(request: Request) -> AsyncClient:
    return cast(AsyncClient, request.app.state.supabase_client)
