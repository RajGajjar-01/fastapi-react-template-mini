from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class UserProfile:
    id: str
    email: str
    full_name: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_row(row: dict[str, Any]) -> "UserProfile":
        return UserProfile(
            id=str(row["id"]),
            email=row["email"],
            full_name=row.get("full_name"),
            avatar_url=row.get("avatar_url"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
