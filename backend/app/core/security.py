import asyncio

import jwt
from jwt import PyJWKClient

from app.core.config import settings

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(
            f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
        )
    return _jwks_client


def verify_token(token: str) -> dict[str, object]:
    signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256"],
        audience="authenticated",
        options={"require": ["exp", "sub"]},
    )
    return payload


async def verify_token_async(token: str) -> dict[str, object]:
    """Verify off the event loop: a cold key cache makes a blocking HTTP fetch."""
    return await asyncio.to_thread(verify_token, token)
