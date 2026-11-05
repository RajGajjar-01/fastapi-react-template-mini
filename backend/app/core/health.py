import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from asyncpg import Pool
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from httpx import AsyncClient

from app.core.config import settings
from app.core.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


async def check_database(pool: Pool) -> dict[str, Any]:
    try:
        async with asyncio.timeout(3):
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
        return {"name": "database", "status": "healthy", "critical": True}
    except Exception:
        logger.warning("Database health check failed", exc_info=True)
        return {"name": "database", "status": "unhealthy", "critical": True}


async def check_supabase(client: AsyncClient, url: str) -> dict[str, Any]:
    try:
        async with asyncio.timeout(5):
            await client.get(url)
        return {"name": "supabase", "status": "healthy", "critical": False}
    except Exception:
        logger.warning("Supabase health check failed", exc_info=True)
        return {"name": "supabase", "status": "unhealthy", "critical": False}


@router.get("/live")
async def liveness() -> JSONResponse:
    return success_response({"status": "alive"})


@router.get("/health")
async def readiness(request: Request) -> JSONResponse:
    results = await asyncio.gather(
        check_database(request.app.state.pool),
        check_supabase(request.app.state.supabase_client, settings.SUPABASE_URL),
    )

    overall = "healthy"
    for r in results:
        if r["status"] != "healthy":
            if r.get("critical"):
                overall = "unhealthy"
            elif overall != "unhealthy":
                overall = "degraded"

    status_code = 200 if overall != "unhealthy" else 503

    return success_response(
        {"status": overall, "timestamp": datetime.now(UTC).isoformat(), "checks": {r["name"]: r["status"] for r in results}},
        status_code=status_code,
    )
