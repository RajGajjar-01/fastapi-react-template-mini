from fastapi.testclient import TestClient

from app.core.rate_limit import SlidingWindowLimiter


def test_limiter_blocks_then_recovers() -> None:
    now = [0.0]
    lim = SlidingWindowLimiter(clock=lambda: now[0])
    assert [lim.hit("k", 3, 60) for _ in range(3)] == [None, None, None]
    assert lim.hit("k", 3, 60) == 60
    now[0] = 30
    assert lim.hit("k", 3, 60) == 30
    now[0] = 61
    assert lim.hit("k", 3, 60) is None


def test_limiter_keys_are_independent_and_memory_is_bounded() -> None:
    lim = SlidingWindowLimiter(max_keys=5, clock=lambda: 0.0)
    assert lim.hit("a", 1, 60) is None
    assert lim.hit("a", 1, 60) is not None
    assert lim.hit("b", 1, 60) is None
    for i in range(50):
        lim.hit(f"flood-{i}", 1, 60)
    assert len(lim._hits) <= 5


def test_validation_errors_do_not_echo_input(client: TestClient) -> None:
    res = client.post("/auth/login", json={"email": "not-an-email", "password": "Sup3rSecret!"})
    assert res.status_code == 422
    assert "Sup3rSecret" not in res.text
    assert "not-an-email" not in res.text
    assert res.json()["error"]["details"][0].keys() == {"loc", "msg", "type"}


def test_unauthenticated_requests_are_refused(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401
    assert client.get("/admin/users").status_code == 401


def test_cors_preflight_for_unknown_origin_gets_no_allow_origin(client: TestClient) -> None:
    res = client.options(
        "/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in res.headers
    ok = client.options(
        "/auth/login",
        headers={"Origin": "http://app.test", "Access-Control-Request-Method": "POST"},
    )
    assert ok.headers["access-control-allow-origin"] == "http://app.test"
