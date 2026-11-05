import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.dependencies import (
    get_current_user,
    get_user_repository,
    require_admin,
    require_moderator_or_admin,
)
from app.core.response import error_response, success_response
from app.models.user import UserProfile
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AssignRoleRequest

router = APIRouter(tags=["admin"])

MAX_PAGE_SIZE = 200


def _serialize(profile: UserProfile) -> dict[str, Any]:
    return {
        "user_id": profile.id,
        "email": profile.email,
        "full_name": profile.full_name,
        "role": profile.role,
        "created_at": profile.created_at.isoformat(),
    }


@router.get("/users")
async def list_users(
    limit: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_moderator_or_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    users = await user_repo.get_page(limit, offset)
    total = await user_repo.count()
    return success_response(
        [_serialize(u) for u in users],
        meta={"limit": limit, "offset": offset, "total": total},
    )


@router.patch("/users/{user_id}/role")
async def assign_role(
    user_id: uuid.UUID,
    body: AssignRoleRequest,
    current_user: dict[str, str | object] = Depends(get_current_user),
    _: str = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    # Compare parsed UUIDs: upper-case or brace spellings of the caller's own
    # id must not slip past the self-change check.
    try:
        own_id = uuid.UUID(cast(str, current_user["sub"]))
    except ValueError:
        own_id = None
    if own_id is not None and user_id == own_id:
        return error_response(400, "CANNOT_MODIFY_OWN_ROLE", "You cannot change your own role")
    profile = await user_repo.assign_role(str(user_id), body.role)
    if profile is None:
        return error_response(404, "USER_NOT_FOUND", "User not found")
    return success_response(_serialize(profile))
