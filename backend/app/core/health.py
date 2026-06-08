import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.config import settings
from app.core.response import success_response

router = APIRouter(tags=["Health"])


async def check_database(pool) -> dict:
    try:
        async with asyncio.timeout(3):
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
        return {"name": "database", "status": "healthy", "critical": True}
    except Exception as e:
        return {"name": "database", "status": "unhealthy", "critical": True, "error": str(e)}


async def check_supabase(client, url) -> dict:
    try:
        async with asyncio.timeout(5):
            await client.get(url)
        return {"name": "supabase", "status": "healthy", "critical": False}
    except Exception as e:
        return {"name": "supabase", "status": "unhealthy", "critical": False, "error": str(e)}


@router.get("/live")
async def liveness():
    return success_response({"status": "alive"})


@router.get("/health")
async def readiness(request: Request):
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
        {"status": overall, "timestamp": datetime.now(timezone.utc).isoformat(), "checks": {r["name"]: r["status"] for r in results}},
        status_code=status_code,
    )
