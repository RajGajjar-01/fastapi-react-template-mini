import logging
from typing import Any, Literal, cast

import httpx
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from httpx import AsyncClient
from jwt import PyJWTError

from app.core.config import settings
from app.core.dependencies import (
    get_current_user,
    get_supabase_client,
    get_user_repository,
    require_trusted_origin,
)
from app.core.rate_limit import client_ip, enforce_key_limit, rate_limit_by_ip
from app.core.response import error_response, success_response
from app.core.security import verify_token_async
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    UpdateProfileRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

# Supabase error codes whose message helps a user fix their input. Other
# signup errors (for example "user already registered") get a generic message
# so the endpoint does not reveal which emails have accounts.
_SAFE_SIGNUP_CODES = {"weak_password", "validation_failed", "email_address_invalid", "signup_disabled"}

ACCESS_TOKEN_MAX_AGE = 600  # keep in step with the Supabase JWT expiry
REFRESH_TOKEN_MAX_AGE = 2592000


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
        max_age=ACCESS_TOKEN_MAX_AGE,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=samesite,
        max_age=REFRESH_TOKEN_MAX_AGE,
    )


def delete_auth_cookies(response: Response) -> None:
    samesite = _samesite()
    response.delete_cookie("access_token", httponly=True, secure=settings.COOKIE_SECURE, samesite=samesite)
    response.delete_cookie("refresh_token", httponly=True, secure=settings.COOKIE_SECURE, samesite=samesite)


def _gotrue_headers(request: Request, bearer: str | None = None, with_json: bool = True) -> dict[str, str]:
    headers = {"apikey": settings.SUPABASE_PUBLISHABLE_KEY}
    if with_json:
        headers["Content-Type"] = "application/json"
    if bearer is not None:
        headers["Authorization"] = f"Bearer {bearer}"
    # Pass the real client address so Supabase can apply per-client limits.
    # It only trusts this header if its operator configured it to.
    ip = client_ip(request)
    if ip != "unknown":
        headers["X-Forwarded-For"] = ip
    return headers


def _rate_limited_upstream(resp: httpx.Response) -> JSONResponse | None:
    # Pass a Supabase rate limit through as a 429 instead of hiding it
    # behind a credentials or session error.
    if resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return error_response(429, "RATE_LIMITED", "Too many requests, please try again later")
    return None


async def _verified_payload(access_token: str) -> dict[str, object] | None:
    try:
        return await verify_token_async(access_token)
    except PyJWTError:
        logger.warning("Access token from the auth service failed verification", exc_info=True)
        return None


async def _gotrue_logout(
    client: AsyncClient,
    request: Request,
    access_token: str,
    scope: Literal["global", "local", "others"] | None = None,
) -> bool:
    try:
        resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/logout",
            params={"scope": scope} if scope else None,
            headers=_gotrue_headers(request, bearer=access_token, with_json=False),
        )
    except httpx.HTTPError:
        logger.warning("Auth service logout request failed", exc_info=True)
        return False
    return resp.status_code in (200, 204)


@router.post("/login", dependencies=[Depends(rate_limit_by_ip("login", 20, 60))])
async def login(
    body: LoginRequest,
    request: Request,
    client: AsyncClient = Depends(get_supabase_client),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    enforce_key_limit("login", body.email, 10, 900)

    supabase_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "password"},
        headers=_gotrue_headers(request),
        json={"email": body.email, "password": body.password},
    )

    if (limited := _rate_limited_upstream(supabase_resp)) is not None:
        return limited
    if supabase_resp.status_code != 200:
        return error_response(401, "INVALID_CREDENTIALS", "Invalid email or password")

    tokens = supabase_resp.json()
    payload = await _verified_payload(tokens["access_token"])
    if payload is None:
        return error_response(502, "UPSTREAM_ERROR", "Could not verify the session from the auth service")
    token_email = payload.get("email")
    if not isinstance(token_email, str) or not token_email:
        return error_response(401, "INVALID_CREDENTIALS", "Invalid email or password")

    await user_repo.upsert(
        user_id=cast(str, payload["sub"]),
        email=token_email,
    )

    resp = success_response({"message": "Logged in", "email": body.email})
    set_auth_cookies(resp, tokens)
    return resp


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_by_ip("signup", 10, 60))],
)
async def signup(
    body: SignupRequest,
    request: Request,
    client: AsyncClient = Depends(get_supabase_client),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    supabase_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/signup",
        headers=_gotrue_headers(request),
        json={"email": body.email, "password": body.password},
    )

    if (limited := _rate_limited_upstream(supabase_resp)) is not None:
        return limited
    if supabase_resp.status_code != 200:
        try:
            err_body = supabase_resp.json()
        except ValueError:
            err_body = {}
        if not isinstance(err_body, dict):
            err_body = {}
        logger.warning("Supabase signup failed (%s, code=%s)", supabase_resp.status_code, err_body.get("error_code"))
        message = err_body.get("msg") or err_body.get("error_description") or err_body.get("message")
        if err_body.get("error_code") in _SAFE_SIGNUP_CODES and isinstance(message, str):
            detail = message
        else:
            detail = "Signup could not be completed"
        return error_response(400, "SIGNUP_FAILED", detail)

    data = supabase_resp.json()
    auto_confirmed = bool(data.get("access_token"))

    if auto_confirmed:
        payload = await _verified_payload(data["access_token"])
        token_email = payload.get("email") if payload else None
        if payload is not None and isinstance(token_email, str):
            await user_repo.upsert(
                user_id=cast(str, payload["sub"]),
                email=token_email,
                full_name=body.full_name,
            )
            resp = success_response(
                {"message": "Signed up", "email": body.email},
                status_code=status.HTTP_201_CREATED,
            )
            set_auth_cookies(resp, data)
            return resp

    return success_response(
        {"message": "Confirmation email sent", "email": body.email},
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/refresh",
    dependencies=[Depends(require_trusted_origin), Depends(rate_limit_by_ip("refresh", 60, 60))],
)
async def refresh(
    request: Request,
    client: AsyncClient = Depends(get_supabase_client),
) -> JSONResponse:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return error_response(401, "NOT_AUTHENTICATED", "Not authenticated")

    supabase_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "refresh_token"},
        headers=_gotrue_headers(request),
        json={"refresh_token": refresh_token},
    )

    if (limited := _rate_limited_upstream(supabase_resp)) is not None:
        return limited
    if supabase_resp.status_code != 200:
        return error_response(401, "SESSION_EXPIRED", "Session expired, please log in again")

    tokens = supabase_resp.json()

    resp = success_response({"message": "Refreshed"})
    set_auth_cookies(resp, tokens)
    return resp


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin)],
)
async def logout(
    request: Request,
    client: AsyncClient = Depends(get_supabase_client),
) -> Response:
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    revoked = False
    if access_token:
        revoked = await _gotrue_logout(client, request, access_token)

    if not revoked and refresh_token:
        # The access cookie lives 10 minutes, so a late logout has none (or an
        # expired one). Exchange the refresh token for a fresh session and
        # sign that session out, which revokes the user's refresh tokens.
        try:
            refreshed = await client.post(
                f"{settings.SUPABASE_URL}/auth/v1/token",
                params={"grant_type": "refresh_token"},
                headers=_gotrue_headers(request),
                json={"refresh_token": refresh_token},
            )
        except httpx.HTTPError:
            refreshed = None
        if refreshed is not None and refreshed.status_code == 200:
            fresh_access = refreshed.json().get("access_token")
            if isinstance(fresh_access, str):
                revoked = await _gotrue_logout(client, request, fresh_access)

    if (access_token or refresh_token) and not revoked:
        logger.warning("Logout could not revoke the session at the auth service")

    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    delete_auth_cookies(resp)
    return resp


def _profile_payload(profile: Any) -> dict[str, Any]:
    return {
        "user_id": profile.id,
        "email": profile.email,
        "full_name": profile.full_name,
        "avatar_url": profile.avatar_url,
        "role": profile.role,
    }


@router.get("/me")
async def get_me(
    current_user: dict[str, str | object] = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> JSONResponse:
    user_id = cast(str, current_user["sub"])
    profile = await user_repo.get_by_id(user_id)
    if profile is None:
        return error_response(404, "PROFILE_NOT_FOUND", "Profile not found")
    return success_response(_profile_payload(profile))


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
    return success_response(_profile_payload(profile))


@router.post("/forgot-password", dependencies=[Depends(rate_limit_by_ip("forgot", 10, 600))])
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    client: AsyncClient = Depends(get_supabase_client),
) -> JSONResponse:
    # Each request sends a real email, so also cap the mail per address.
    enforce_key_limit("forgot", body.email, 3, 3600)

    resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/recover",
        headers=_gotrue_headers(request),
        json={"email": body.email},
    )

    if (limited := _rate_limited_upstream(resp)) is not None:
        return limited
    if resp.status_code != 200:
        return error_response(400, "RESET_FAILED", "Failed to send reset email")

    return success_response({"message": "If the email exists, a reset link has been sent"})


@router.post("/reset-password", dependencies=[Depends(rate_limit_by_ip("reset", 10, 60))])
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    client: AsyncClient = Depends(get_supabase_client),
) -> JSONResponse:
    # Exchange the one-time recovery token hash from the email link for a
    # session (POST /auth/v1/verify). The reset email template must link to
    # the app with ?token_hash={{ .TokenHash }} (see README).
    verify_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/verify",
        headers=_gotrue_headers(request),
        json={"type": "recovery", "token_hash": body.token},
    )

    if (limited := _rate_limited_upstream(verify_resp)) is not None:
        return limited
    if verify_resp.status_code != 200:
        return error_response(400, "INVALID_TOKEN", "Invalid or expired reset token")

    access_token = verify_resp.json().get("access_token")
    if not isinstance(access_token, str):
        return error_response(400, "INVALID_TOKEN", "Invalid or expired reset token")

    update_resp = await client.put(
        f"{settings.SUPABASE_URL}/auth/v1/user",
        headers=_gotrue_headers(request, bearer=access_token),
        json={"password": body.password},
    )

    if update_resp.status_code != 200:
        return error_response(400, "PASSWORD_UPDATE_FAILED", "Failed to update password")

    # A reset means the old password may be compromised: end every session,
    # including the recovery session. The user signs in again.
    if not await _gotrue_logout(client, request, access_token, scope="global"):
        logger.warning("Could not revoke sessions after password reset")

    return success_response({"message": "Password updated successfully"})


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: dict[str, str | object] = Depends(get_current_user),
    client: AsyncClient = Depends(get_supabase_client),
) -> JSONResponse:
    email = current_user.get("email")
    if not isinstance(email, str) or not email:
        return error_response(400, "INVALID_CURRENT_PASSWORD", "Current password is incorrect")

    # This endpoint checks a password guess, so it gets its own per-user limit.
    enforce_key_limit("change-password", cast(str, current_user["sub"]), 5, 900)

    auth_resp = await client.post(
        f"{settings.SUPABASE_URL}/auth/v1/token",
        params={"grant_type": "password"},
        headers=_gotrue_headers(request),
        json={"email": email, "password": body.current_password},
    )

    if (limited := _rate_limited_upstream(auth_resp)) is not None:
        return limited
    if auth_resp.status_code != 200:
        return error_response(400, "INVALID_CURRENT_PASSWORD", "Current password is incorrect")

    session = auth_resp.json()
    access_token = session["access_token"]

    update_resp = await client.put(
        f"{settings.SUPABASE_URL}/auth/v1/user",
        headers=_gotrue_headers(request, bearer=access_token),
        json={"password": body.new_password},
    )

    if update_resp.status_code != 200:
        return error_response(400, "PASSWORD_UPDATE_FAILED", "Failed to update password")

    # Sign out every other session so a stolen refresh token stops working.
    if not await _gotrue_logout(client, request, access_token, scope="others"):
        logger.warning("Could not revoke other sessions after password change")

    resp = success_response({"message": "Password updated successfully"})
    set_auth_cookies(resp, session)
    return resp
