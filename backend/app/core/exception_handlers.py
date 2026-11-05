import sys
import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import error_response


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    headers = dict(exc.headers) if exc.headers else None
    if isinstance(exc.detail, dict):
        return error_response(
            status_code=exc.status_code,
            title=exc.detail.get("title", str(exc.status_code)),
            detail=exc.detail.get("detail", str(exc.detail)),
            error_type=exc.detail.get("type", "about:blank"),
            headers=headers,
        )

    return error_response(
        status_code=exc.status_code,
        title=str(exc.status_code),
        detail=exc.detail,
        headers=headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Return only where and why a field failed. The default error list also
    # echoes the submitted value ("input"), which can be a password.
    details = [
        {"loc": list(err.get("loc", ())), "msg": err.get("msg", ""), "type": err.get("type", "")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "about:blank",
                "title": "VALIDATION_ERROR",
                "status": 422,
                "detail": "Request validation failed",
                "details": details,
            },
            "meta": None,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    traceback.print_exc(file=sys.stderr)
    return error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="INTERNAL_ERROR",
        detail="Internal server error",
    )
