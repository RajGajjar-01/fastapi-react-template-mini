from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asyncpg import Connection, Pool


class BaseRepository:
    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _connection(self) -> AsyncGenerator[Connection, None]:
        async with self._pool.acquire() as conn:
            yield conn