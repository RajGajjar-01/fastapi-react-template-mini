"""Small in-process sliding-window rate limiter for the auth endpoints.

State is kept per worker process. With several workers or replicas, add a
limit at the proxy as well. The Supabase auth service applies its own limits,
but it sees only this backend's address, so one client could use up the
shared budget unless the backend limits clients first.
"""

import math
import time
from collections import deque
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, status

from app.core.config import settings

Clock = Callable[[], float]


class SlidingWindowLimiter:
    def __init__(self, max_keys: int = 10_000, clock: Clock = time.monotonic) -> None:
        self._hits: dict[str, tuple[deque[float], float]] = {}
        self._max_keys = max_keys
        self._clock = clock

    def clear(self) -> None:
        self._hits.clear()

    def hit(self, key: str, limit: int, window: float) -> int | None:
        """Record a hit. Return None if allowed, else seconds to wait."""
        now = self._clock()
        hits, _ = self._hits.get(key, (deque(), window))
        while hits and now - hits[0] >= window:
            hits.popleft()
        if len(hits) >= limit:
            self._hits[key] = (hits, window)
            return max(1, math.ceil(window - (now - hits[0])))
        hits.append(now)
        self._hits[key] = (hits, window)
        if len(self._hits) > self._max_keys:
            self._purge(now)
        return None

    def _purge(self, now: float) -> None:
        for key in [k for k, (h, w) in self._hits.items() if not h or now - h[-1] >= w]:
            del self._hits[key]
        while len(self._hits) > self._max_keys:
            del self._hits[next(iter(self._hits))]


limiter = SlidingWindowLimiter()


def _too_many(retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "title": "RATE_LIMITED",
            "detail": "Too many requests, please try again later",
            "type": "about:blank",
            "status": 429,
        },
        headers={"Retry-After": str(retry_after)},
    )


def client_ip(request: Request) -> str:
    # Behind a proxy, run uvicorn with --proxy-headers and set
    # FORWARDED_ALLOW_IPS so that request.client holds the real client address.
    return request.client.host if request.client else "unknown"


def rate_limit_by_ip(name: str, limit: int, window: float) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        retry_after = limiter.hit(f"{name}:ip:{client_ip(request)}", limit, window)
        if retry_after is not None:
            raise _too_many(retry_after)

    return dependency


def enforce_key_limit(name: str, key: str, limit: int, window: float) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    retry_after = limiter.hit(f"{name}:key:{key.strip().lower()}", limit, window)
    if retry_after is not None:
        raise _too_many(retry_after)

