from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.conftest import USER_ID, FakeRepo, FakeResponse, FakeSupabase, Keys

ALLOWED = "http://app.test"


def _session(keys: Keys, sub: str = USER_ID, email: str = "a@example.com") -> dict[str, str]:
    return {"access_token": keys.token({"sub": sub, "email": email}), "refresh_token": "refresh-new"}


# ── login ────────────────────────────────────────────────────────────────


def test_login_sets_cookies_and_uses_verified_email(client: TestClient, supabase: FakeSupabase, repo: FakeRepo, keys: Keys) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(200, _session(keys, email="real@example.com"))
    res = client.post("/auth/login", json={"email": "typed@example.com", "password": "pw"})
    assert res.status_code == 200
    assert repo.upserts[0]["email"] == "real@example.com"
    assert "access_token" in res.cookies and "refresh_token" in res.cookies


def test_login_passes_client_address_to_supabase(client: TestClient, supabase: FakeSupabase, keys: Keys) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(400, {})
    client.post("/auth/login", json={"email": "a@example.com", "password": "pw"})
    assert supabase.calls[0].headers["X-Forwarded-For"] == "testclient"


def test_login_maps_upstream_rate_limit_to_429(client: TestClient, supabase: FakeSupabase) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(429, {})
    res = client.post("/auth/login", json={"email": "a@example.com", "password": "pw"})
    assert res.status_code == 429
    assert res.json()["error"]["title"] == "RATE_LIMITED"


def test_login_is_limited_per_email(client: TestClient, supabase: FakeSupabase) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(400, {})
    codes = [client.post("/auth/login", json={"email": "victim@example.com", "password": "x"}).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
    res = client.post("/auth/login", json={"email": "victim@example.com", "password": "x"})
    assert res.headers["Retry-After"].isdigit()


def test_forgot_password_mail_is_limited_per_address(client: TestClient, supabase: FakeSupabase) -> None:
    codes = [client.post("/auth/forgot-password", json={"email": "v@example.com"}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    assert len([c for c in supabase.calls if c.path == "/auth/v1/recover"]) == 3


# ── signup ───────────────────────────────────────────────────────────────


def test_signup_hides_account_existence(client: TestClient, supabase: FakeSupabase) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(422, {"error_code": "user_already_exists", "msg": "User already registered"})
    res = client.post("/auth/signup", json={"email": "a@example.com", "password": "longenough"})
    assert res.status_code == 400
    assert "already" not in res.text


def test_signup_relays_password_policy_message(client: TestClient, supabase: FakeSupabase) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(422, {"error_code": "weak_password", "msg": "Password is too weak"})
    res = client.post("/auth/signup", json={"email": "a@example.com", "password": "longenough"})
    assert res.json()["error"]["detail"] == "Password is too weak"


def test_signup_survives_non_json_error_body(client: TestClient, supabase: FakeSupabase) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(502, bad_json=True)
    res = client.post("/auth/signup", json={"email": "a@example.com", "password": "longenough"})
    assert res.status_code == 400


def test_signup_enforces_password_length_without_echoing_it(client: TestClient, supabase: FakeSupabase) -> None:
    res = client.post("/auth/signup", json={"email": "a@example.com", "password": "short"})
    assert res.status_code == 422
    assert "short" not in res.text.replace("too_short", "").replace("String should have at least", "")
    assert supabase.calls == []


# ── profile input ────────────────────────────────────────────────────────


def _as_user(client: TestClient, keys: Keys) -> None:
    client.cookies.set("access_token", keys.token())


def test_profile_rejects_non_http_avatar(client: TestClient, repo: FakeRepo, keys: Keys) -> None:
    repo.add(USER_ID)
    _as_user(client, keys)
    res = client.patch("/auth/me", json={"avatar_url": "javascript:alert(1)"})
    assert res.status_code == 422
    assert "javascript" not in res.text


def test_profile_rejects_oversized_fields(client: TestClient, repo: FakeRepo, keys: Keys) -> None:
    repo.add(USER_ID)
    _as_user(client, keys)
    assert client.patch("/auth/me", json={"full_name": "x" * 201}).status_code == 422
    assert client.patch("/auth/me", json={"avatar_url": "https://e.test/" + "a" * 2100}).status_code == 422
    ok = client.patch("/auth/me", json={"full_name": "  Ada  ", "avatar_url": "https://e.test/a.png"})
    assert ok.status_code == 200
    assert ok.json()["data"]["full_name"] == "Ada"


# ── logout and cross-site requests ───────────────────────────────────────


def test_logout_revokes_with_valid_access_token(client: TestClient, supabase: FakeSupabase, keys: Keys) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(204, {})
    client.cookies.set("access_token", keys.token())
    client.cookies.set("refresh_token", "refresh-old")
    assert client.post("/auth/logout").status_code == 204
    assert [c.path for c in supabase.calls] == ["/auth/v1/logout"]


def test_logout_after_access_cookie_expired_still_revokes(client: TestClient, supabase: FakeSupabase, keys: Keys) -> None:
    fresh = keys.token({"sub": USER_ID})

    def handler(method: str, path: str, params: dict | None, body: dict | None) -> FakeResponse:
        if path == "/auth/v1/token":
            return FakeResponse(200, {"access_token": fresh, "refresh_token": "r2"})
        return FakeResponse(204, {})

    supabase.handler = handler
    client.cookies.set("refresh_token", "refresh-old")  # no access_token cookie
    res = client.post("/auth/logout")
    assert res.status_code == 204
    assert [c.path for c in supabase.calls] == ["/auth/v1/token", "/auth/v1/logout"]
    assert supabase.calls[1].headers["Authorization"] == f"Bearer {fresh}"


def test_logout_always_clears_cookies_even_if_revoke_fails(client: TestClient, supabase: FakeSupabase, keys: Keys) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(500, {})
    client.cookies.set("access_token", keys.token())
    res = client.post("/auth/logout")
    assert res.status_code == 204
    assert "access_token=" in res.headers["set-cookie"]


def test_logout_and_refresh_reject_foreign_origin(client: TestClient, supabase: FakeSupabase) -> None:
    client.cookies.set("refresh_token", "r")
    for path in ("/auth/logout", "/auth/refresh"):
        res = client.post(path, headers={"Origin": "https://evil.example"})
        assert res.status_code == 403, path
    assert supabase.calls == []


def test_logout_accepts_allowed_and_missing_origin(client: TestClient, supabase: FakeSupabase) -> None:
    assert client.post("/auth/logout", headers={"Origin": ALLOWED}).status_code == 204
    assert client.post("/auth/logout").status_code == 204


# ── password change and reset ────────────────────────────────────────────


def test_change_password_signs_out_other_sessions(client: TestClient, supabase: FakeSupabase, keys: Keys) -> None:
    session = _session(keys)

    def handler(method: str, path: str, params: dict | None, body: dict | None) -> FakeResponse:
        if path == "/auth/v1/token":
            return FakeResponse(200, session)
        return FakeResponse(200, {}) if path == "/auth/v1/user" else FakeResponse(204, {})

    supabase.handler = handler
    client.cookies.set("access_token", keys.token())
    res = client.post("/auth/change-password", json={"current_password": "old-password", "new_password": "new-password-1"})
    assert res.status_code == 200
    assert [c.path for c in supabase.calls] == ["/auth/v1/token", "/auth/v1/user", "/auth/v1/logout"]
    last = supabase.calls[-1]
    assert last.params == {"scope": "others"}
    assert last.headers["Authorization"] == f"Bearer {session['access_token']}"


def test_change_password_wrong_current_password_changes_nothing(client: TestClient, supabase: FakeSupabase, keys: Keys) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(400, {})
    client.cookies.set("access_token", keys.token())
    res = client.post("/auth/change-password", json={"current_password": "wrong", "new_password": "new-password-1"})
    assert res.status_code == 400
    assert [c.path for c in supabase.calls] == ["/auth/v1/token"]


def test_change_password_guesses_are_limited(client: TestClient, supabase: FakeSupabase, keys: Keys) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(400, {})
    client.cookies.set("access_token", keys.token())
    body = {"current_password": "guess", "new_password": "new-password-1"}
    codes = [client.post("/auth/change-password", json=body).status_code for _ in range(6)]
    assert codes == [400] * 5 + [429]


def test_reset_password_uses_verify_endpoint_and_revokes_sessions(client: TestClient, supabase: FakeSupabase) -> None:
    def handler(method: str, path: str, params: dict | None, body: dict | None) -> FakeResponse:
        if path == "/auth/v1/verify":
            return FakeResponse(200, {"access_token": "recovery-session"})
        return FakeResponse(200, {}) if path == "/auth/v1/user" else FakeResponse(204, {})

    supabase.handler = handler
    res = client.post("/auth/reset-password", json={"token": "hash123", "password": "new-password-1"})
    assert res.status_code == 200
    assert supabase.calls[0].path == "/auth/v1/verify"
    assert supabase.calls[0].json == {"type": "recovery", "token_hash": "hash123"}
    assert supabase.calls[-1].params == {"scope": "global"}


def test_reset_password_invalid_token(client: TestClient, supabase: FakeSupabase) -> None:
    supabase.handler = lambda m, p, params, body: FakeResponse(403, {})
    res = client.post("/auth/reset-password", json={"token": "bad", "password": "new-password-1"})
    assert res.status_code == 400
    assert [c.path for c in supabase.calls] == ["/auth/v1/verify"]


# ── settings ─────────────────────────────────────────────────────────────


def test_wildcard_origin_is_rejected() -> None:
    import pytest
    from pydantic import ValidationError

    base = {
        "SUPABASE_URL": "http://x",
        "SUPABASE_PUBLISHABLE_KEY": "k",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_SERVER": "h",
    }
    for bad in (["*"], ["app.test"]):
        with pytest.raises(ValidationError):
            Settings(ALLOWED_ORIGINS=bad, **base)  # type: ignore[arg-type]
    assert Settings(ALLOWED_ORIGINS=["https://app.test"], **base).ALLOWED_ORIGINS == ["https://app.test"]  # type: ignore[arg-type]
