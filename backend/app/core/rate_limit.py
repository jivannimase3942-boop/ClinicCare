import time
import threading
from typing import Dict, Tuple, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SlidingWindowRateLimiter:
    """
    Thread-safe, in-memory sliding-window rate limiter for FastAPI.
    Supports endpoint category rules and automatic memory cleanup.
    """
    def __init__(self):
        self._lock = threading.Lock()
        # Key: (ip, category) -> List of timestamps
        self._requests: Dict[Tuple[str, str], List[float]] = {}
        self._last_cleanup = time.time()
        self.enabled = True

    def _cleanup_expired(self, now: float, window: float = 60.0):
        """Purge entries older than window to prevent unbounded memory growth."""
        if now - self._last_cleanup < 30.0:
            return
        keys_to_remove = []
        for key, timestamps in self._requests.items():
            self._requests[key] = [t for t in timestamps if now - t < window]
            if not self._requests[key]:
                keys_to_remove.append(key)
        for k in keys_to_remove:
            del self._requests[k]
        self._last_cleanup = now

    def is_allowed(
        self,
        key: str,
        category: str,
        max_requests: int,
        window_seconds: float = 60.0,
    ) -> Tuple[bool, int, int]:
        """
        Returns (is_allowed, remaining_requests, retry_after_seconds)
        """
        if not self.enabled:
            return True, max_requests, 0

        now = time.time()
        dict_key = (key, category)

        with self._lock:
            self._cleanup_expired(now, window_seconds)

            timestamps = self._requests.get(dict_key, [])
            # Filter timestamps within current window
            valid_timestamps = [t for t in timestamps if now - t < window_seconds]

            if len(valid_timestamps) >= max_requests:
                oldest_timestamp = valid_timestamps[0]
                retry_after = max(1, int(window_seconds - (now - oldest_timestamp)))
                self._requests[dict_key] = valid_timestamps
                return False, 0, retry_after

            valid_timestamps.append(now)
            self._requests[dict_key] = valid_timestamps
            remaining = max(0, max_requests - len(valid_timestamps))
            return True, remaining, 0

    def reset(self):
        """Reset state (useful in test teardowns)."""
        with self._lock:
            self._requests.clear()


limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Rate Limiting Middleware.
    Protects authentication, AI generation, and general APIs against abuse.
    """

    # Category thresholds: (limit_per_minute, window_seconds)
    LIMITS = {
        "auth": (20, 60.0),       # 20 attempts / min for login, registration, OTP
        "ai": (30, 60.0),         # 30 AI generations / min
        "general": (200, 60.0),   # 200 requests / min for general API
    }

    def _get_client_ip(self, request: Request) -> str:
        from app.core.security import get_client_ip
        return get_client_ip(request)

    def _categorize_path(self, path: str) -> Optional[str]:
        # Health checks, static docs, and root endpoints are unthrottled
        if path in ("/", "/health", "/api/health", "/docs", "/redoc", "/openapi.json"):
            return None
        if path.startswith("/whatsapp-webhook"):
            return None

        # High-security endpoints
        if any(path.startswith(p) for p in (
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/google",
            "/api/auth/logout",
            "/api/auth/change-password",
            "/api/security/change-password",
        )):
            return "auth"

        # AI and voice endpoints
        if path.startswith("/api/ai/chat") or path.startswith("/api/voice/request"):
            return "ai"

        # All other API endpoints
        if path.startswith("/api/"):
            return "general"

        return None

    async def dispatch(self, request: Request, call_next) -> Response:
        category = self._categorize_path(request.url.path)
        if not category:
            return await call_next(request)

        # Allow test suite bypass if explicitly flagged or under standard testclient unless rate limit test requested
        if request.headers.get("X-Rate-Limit-Test") != "true":
            # Check if running under automated test suite without explicit rate limit test flag
            if request.client and request.client.host == "testclient" and request.headers.get("X-Enforce-Rate-Limit") != "true":
                return await call_next(request)

        client_ip = self._get_client_ip(request)
        max_req, window = self.LIMITS.get(category, (120, 60.0))

        allowed, remaining, retry_after = limiter.is_allowed(
            key=client_ip,
            category=category,
            max_requests=max_req,
            window_seconds=window,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_req),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
