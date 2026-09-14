from fastapi import APIRouter, Depends
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


def _serialize(profile: UserProfile) -> dict:
    return {
        "user_id": profile.id,
        "email": profile.email,
        "full_name": profile.full_name,
        "role": profile.role,
        "created_at": profile.created_at.isoformat(),
    }


@router.get("/users")
async def list_users(
    _: str = Depends(require_moderator_or_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    users = await user_repo.get_all()
    return success_response([_serialize(u) for u in users])


@router.patch("/users/{user_id}/role")
async def assign_role(
    user_id: str,
    body: AssignRoleRequest,
    current_user: dict[str, str | object] = Depends(get_current_user),
    _: str = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    if user_id == current_user["sub"]:
        return error_response(400, "CANNOT_MODIFY_OWN_ROLE", "You cannot change your own role")
    profile = await user_repo.assign_role(user_id, body.role)
    if profile is None:
        return error_response(404, "USER_NOT_FOUND", "User not found")
    return success_response(_serialize(profile))
