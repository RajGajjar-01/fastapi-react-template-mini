import asyncpg
from fastapi import Request

from app.core.config import settings


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
        min_size=settings.DB_POOL_SIZE,
        max_size=settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW,
        timeout=settings.DB_POOL_TIMEOUT,
    )


async def get_db(request: Request):
    async with request.app.state.pool.acquire() as connection:
        yield connection
