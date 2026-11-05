import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Settings are read when app.core.config is imported, so set them first.
os.environ.update(
    {
        "SUPABASE_URL": "http://supabase.test",
        "SUPABASE_PUBLISHABLE_KEY": "pk-test",
        "ALLOWED_ORIGINS": '["http://app.test"]',
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_SERVER": "localhost",
        "COOKIE_SECURE": "false",
    }
)

import jwt  # noqa: E402
import pytest  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core import security  # noqa: E402
from app.core.dependencies import get_supabase_client, get_user_repository  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import UserProfile  # noqa: E402

USER_ID = "11111111-1111-4111-8111-111111111111"
OTHER_ID = "22222222-2222-4222-8222-222222222222"


class FakeResponse:
    def __init__(self, status_code: int = 200, body: Any = None, bad_json: bool = False) -> None:
        self.status_code = status_code
        self._body = body if body is not None else {}
        self._bad_json = bad_json

    def json(self) -> Any:
        if self._bad_json:
            raise ValueError("not json")
        return self._body


Handler = Callable[[str, str, dict[str, Any] | None, dict[str, Any] | None], FakeResponse]


@dataclass
class Call:
    method: str
    path: str
    params: dict[str, Any] | None
    headers: dict[str, str]
    json: dict[str, Any] | None


class FakeSupabase:
    """Stands in for the httpx client that talks to Supabase Auth."""

    def __init__(self) -> None:
        self.calls: list[Call] = []
        self.handler: Handler = lambda method, path, params, body: FakeResponse(200, {})

    async def _send(self, method: str, url: str, params: Any, headers: Any, json: Any) -> FakeResponse:
        path = url.removeprefix("http://supabase.test")
        self.calls.append(Call(method, path, params, dict(headers or {}), json))
        return self.handler(method, path, params, json)

    async def post(self, url: str, params: Any = None, headers: Any = None, json: Any = None) -> FakeResponse:
        return await self._send("POST", url, params, headers, json)

    async def put(self, url: str, params: Any = None, headers: Any = None, json: Any = None) -> FakeResponse:
        return await self._send("PUT", url, params, headers, json)


@dataclass
class FakeRepo:
    profiles: dict[str, UserProfile] = field(default_factory=dict)
    upserts: list[dict[str, Any]] = field(default_factory=list)
    role_changes: list[tuple[str, str]] = field(default_factory=list)

    def add(self, user_id: str, role: str = "user", email: str = "a@example.com") -> UserProfile:
        now = datetime.now(UTC)
        profile = UserProfile(user_id, email, None, None, role, now, now)
        self.profiles[user_id] = profile
        return profile

    async def get_by_id(self, user_id: str) -> UserProfile | None:
        return self.profiles.get(str(user_id))

    async def get_page(self, limit: int, offset: int) -> list[UserProfile]:
        return list(self.profiles.values())[offset : offset + limit]

    async def count(self) -> int:
        return len(self.profiles)

    async def upsert(self, user_id: str, email: str, full_name: str | None = None, avatar_url: str | None = None) -> UserProfile:
        self.upserts.append({"user_id": user_id, "email": email, "full_name": full_name})
        return self.profiles.get(user_id) or self.add(user_id, email=email)

    async def update_profile(self, user_id: str, full_name: str | None, avatar_url: str | None) -> UserProfile | None:
        profile = self.profiles.get(user_id)
        if profile:
            profile.full_name, profile.avatar_url = full_name, avatar_url
        return profile

    async def assign_role(self, user_id: str, role: str) -> UserProfile | None:
        profile = self.profiles.get(user_id)
        if profile:
            profile.role = role
            self.role_changes.append((user_id, role))
        return profile


class _SigningKey:
    def __init__(self, key: Any) -> None:
        self.key = key


class _FakeJwks:
    def __init__(self, public_key: Any) -> None:
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> _SigningKey:
        return _SigningKey(self._public_key)


class Keys:
    def __init__(self) -> None:
        self.private = ec.generate_private_key(ec.SECP256R1())
        self.public = self.private.public_key()

    def token(self, claims: dict[str, Any] | None = None, **overrides: Any) -> str:
        base: dict[str, Any] = {
            "sub": USER_ID,
            "email": "a@example.com",
            "aud": "authenticated",
            "exp": int(datetime.now(UTC).timestamp()) + 600,
            "app_metadata": {"user_role": "user"},
        }
        base.update(claims or {})
        for key, value in overrides.items():
            if value is None:
                base.pop(key, None)
            else:
                base[key] = value
        return jwt.encode(base, self.private, algorithm="ES256")


@pytest.fixture(scope="session")
def keys() -> Keys:
    return Keys()


@pytest.fixture(autouse=True)
def _fresh_state(monkeypatch: pytest.MonkeyPatch, keys: Keys) -> Iterator[None]:
    monkeypatch.setattr(security, "_get_jwks_client", lambda: _FakeJwks(keys.public))
    limiter.clear()
    yield
    app.dependency_overrides.clear()
    limiter.clear()


@pytest.fixture(autouse=True)
def supabase() -> FakeSupabase:
    fake = FakeSupabase()
    app.dependency_overrides[get_supabase_client] = lambda: fake
    return fake


@pytest.fixture(autouse=True)
def repo() -> FakeRepo:
    fake = FakeRepo()
    app.dependency_overrides[get_user_repository] = lambda: fake
    return fake


@pytest.fixture
def client() -> TestClient:
    # No `with` block: the lifespan (database pool) is not started.
    return TestClient(app, raise_server_exceptions=False)
