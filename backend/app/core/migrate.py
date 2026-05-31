import asyncio
from pathlib import Path

import asyncpg

from app.core.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


async def ensure_migrations_table(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _schema_migrations (
            filename VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


async def get_applied_migrations(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT filename FROM _schema_migrations ORDER BY filename")
    return {row["filename"] for row in rows}


async def get_pending_files() -> list[Path]:
    if not MIGRATIONS_DIR.is_dir():
        return []
    return sorted(MIGRATIONS_DIR.iterdir())


async def apply_migration(conn: asyncpg.Connection, filepath: Path) -> None:
    sql = filepath.read_text()
    async with conn.transaction():
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO _schema_migrations (filename) VALUES ($1)",
            filepath.name,
        )


async def run_migrations(pool: asyncpg.Pool) -> list[str]:
    applied: list[str] = []
    async with pool.acquire() as conn:
        await ensure_migrations_table(conn)
        already = await get_applied_migrations(conn)
        pending = [f for f in await get_pending_files() if f.suffix == ".sql" and f.name not in already]
        if not pending:
            return applied
        for filepath in pending:
            print(f"Applying {filepath.name}...")
            await apply_migration(conn, filepath)
            applied.append(filepath.name)
            print("  Done.")
    return applied


async def main() -> None:
    pool = await asyncpg.create_pool(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
    )
    try:
        applied = await run_migrations(pool)
        if not applied:
            print("No pending migrations.")
        else:
            print(f"Applied: {', '.join(applied)}")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
