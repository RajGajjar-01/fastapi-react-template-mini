import jwt
import pytest
from fastapi.testclient import TestClient

from app.core import security
from tests.conftest import OTHER_ID, USER_ID, FakeRepo, Keys


def test_valid_token_is_accepted(keys: Keys) -> None:
    assert security.verify_token(keys.token())["sub"] == USER_ID


@pytest.mark.parametrize("missing", ["exp", "sub"])
def test_token_without_required_claim_is_rejected(keys: Keys, missing: str) -> None:
    with pytest.raises(jwt.PyJWTError):
        security.verify_token(keys.token(**{missing: None}))


def test_wrong_audience_is_rejected(keys: Keys) -> None:
    with pytest.raises(jwt.PyJWTError):
        security.verify_token(keys.token(aud="anon"))


def test_non_es256_token_is_rejected() -> None:
    forged = jwt.encode({"sub": USER_ID, "aud": "authenticated", "exp": 9999999999}, "x" * 40, algorithm="HS256")
    with pytest.raises(jwt.PyJWTError):
        security.verify_token(forged)


def _login_cookie(client: TestClient, keys: Keys, role: str, sub: str = USER_ID) -> None:
    client.cookies.set("access_token", keys.token({"sub": sub, "app_metadata": {"user_role": role}}))


def test_admin_list_needs_claim_and_database_role(client: TestClient, keys: Keys, repo: FakeRepo) -> None:
    repo.add(USER_ID, role="admin")
    _login_cookie(client, keys, "admin")
    res = client.get("/admin/users")
    assert res.status_code == 200
    assert res.json()["meta"] == {"limit": 50, "offset": 0, "total": 1}


def test_demoted_admin_is_refused_before_token_expiry(client: TestClient, keys: Keys, repo: FakeRepo) -> None:
    repo.add(USER_ID, role="user")  # demoted in the database
    repo.add(OTHER_ID, role="user")
    _login_cookie(client, keys, "admin")  # token still says admin
    res = client.patch(f"/admin/users/{OTHER_ID}/role", json={"role": "admin"})
    assert res.status_code == 403
    assert repo.role_changes == []
    assert client.get("/admin/users").status_code == 403


def test_claim_is_not_enough_without_matching_claim(client: TestClient, keys: Keys, repo: FakeRepo) -> None:
    repo.add(USER_ID, role="admin")  # database says admin, token says user
    _login_cookie(client, keys, "user")
    assert client.get("/admin/users").status_code == 403


def test_role_endpoint_rejects_non_uuid(client: TestClient, keys: Keys, repo: FakeRepo) -> None:
    repo.add(USER_ID, role="admin")
    _login_cookie(client, keys, "admin")
    res = client.patch("/admin/users/not-a-uuid/role", json={"role": "user"})
    assert res.status_code == 422


def test_own_role_cannot_be_changed_with_any_uuid_spelling(client: TestClient, keys: Keys, repo: FakeRepo) -> None:
    repo.add(USER_ID, role="admin")
    _login_cookie(client, keys, "admin")
    for spelling in (USER_ID.upper(), USER_ID.replace("-", "")):
        res = client.patch(f"/admin/users/{spelling}/role", json={"role": "user"})
        assert res.status_code == 400, spelling
    assert repo.role_changes == []


def test_admin_can_change_another_users_role(client: TestClient, keys: Keys, repo: FakeRepo) -> None:
    repo.add(USER_ID, role="admin")
    repo.add(OTHER_ID, role="user")
    _login_cookie(client, keys, "admin")
    res = client.patch(f"/admin/users/{OTHER_ID}/role", json={"role": "moderator"})
    assert res.status_code == 200
    assert repo.role_changes == [(OTHER_ID, "moderator")]


def test_user_list_is_paginated(client: TestClient, keys: Keys, repo: FakeRepo) -> None:
    repo.add(USER_ID, role="admin")
    for i in range(5):
        repo.add(f"3333333{i}-3333-4333-8333-333333333333")
    _login_cookie(client, keys, "admin")
    res = client.get("/admin/users", params={"limit": 2, "offset": 1})
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2
    assert res.json()["meta"] == {"limit": 2, "offset": 1, "total": 6}
    assert client.get("/admin/users", params={"limit": 100000}).status_code == 422
