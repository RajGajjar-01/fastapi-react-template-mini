from httpx import AsyncClient, Limits


def create_supabase_client() -> AsyncClient:
    return AsyncClient(
        limits=Limits(max_connections=20, max_keepalive_connections=10, keepalive_expiry=30),
        timeout=30.0,
    )