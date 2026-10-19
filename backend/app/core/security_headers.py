from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    HTTP Security Headers Middleware for ClinicCare API.
    Enforces defense-in-depth protection against clickjacking, MIME sniffing,
    XSS, and unauthorized framing according to OWASP guidelines.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 1. Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. Prevent clickjacking / framing
        response.headers["X-Frame-Options"] = "DENY"

        # 3. Cross-site scripting filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Strict Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 5. Restrict dangerous browser features / APIs
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # 6. HTTP Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 7. Content Security Policy (CSP)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https:; "
            "connect-src 'self' https: http://localhost:* http://127.0.0.1:*; "
            "frame-ancestors 'none';"
        )

        # 8. Prevent caching of sensitive medical / patient API records
        path = request.url.path
        if any(path.startswith(prefix) for prefix in (
            "/api/auth",
            "/api/patients",
            "/api/reports",
            "/api/billing",
            "/api/clinical",
            "/api/prescriptions",
            "/api/lab",
            "/api/admin",
            "/api/security",
        )):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        # 9. Mask server signature
        if "server" in response.headers:
            del response.headers["server"]

        return response
