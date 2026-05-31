from app.models.user import UserProfile
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: str) -> UserProfile | None:
        async with self._connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, full_name, avatar_url, created_at, updated_at FROM profiles WHERE id = $1",
                user_id,
            )
        if row is None:
            return None
        return UserProfile.from_row(dict(row))

    async def get_by_email(self, email: str) -> UserProfile | None:
        async with self._connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, full_name, avatar_url, created_at, updated_at FROM profiles WHERE email = $1",
                email,
            )
        if row is None:
            return None
        return UserProfile.from_row(dict(row))

    async def upsert(
        self,
        user_id: str,
        email: str,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> UserProfile:
        async with self._connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO profiles (id, email, full_name, avatar_url)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    updated_at = NOW()
                RETURNING *
                """,
                user_id,
                email,
                full_name,
                avatar_url,
            )
        return UserProfile.from_row(dict(row))

    async def update_profile(
        self,
        user_id: str,
        full_name: str | None,
        avatar_url: str | None,
    ) -> UserProfile | None:
        async with self._connection() as conn:
            row = await conn.fetchrow(
                "UPDATE profiles SET full_name=$2, avatar_url=$3 WHERE id=$1 RETURNING *",
                user_id,
                full_name,
                avatar_url,
            )
        if row is None:
            return None
        return UserProfile.from_row(dict(row))
