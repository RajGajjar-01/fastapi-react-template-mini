from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # X-Content-Type-Options: Prevents the browser from MIME-sniffing a response.
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: Prevents clickjacking by not allowing the page to be rendered in a frame.
        response.headers["X-Frame-Options"] = "DENY"
        
        # Strict-Transport-Security: Forces HTTPS connections.
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-XSS-Protection: Enables the Cross-site scripting (XSS) filter.
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy: Helps prevent XSS and other code injection attacks.
        # This is a basic one, can be expanded.
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        
        return response
