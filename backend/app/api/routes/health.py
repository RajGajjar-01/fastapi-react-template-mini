from fastapi import APIRouter
from app.core.security import limiter
from starlette.requests import Request

router = APIRouter()

@router.get("/health")
@limiter.limit("5/minute")
async def health_check(request: Request):
    """
    Health check endpoint to verify backend status.
    Rate limited to 5 requests per minute.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "FastAPI backend is running successfully"
    }
