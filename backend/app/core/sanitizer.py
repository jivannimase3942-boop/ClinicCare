import re
import json
from typing import Any, Union, Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Regex patterns for dangerous XSS constructs
SCRIPT_TAG_REGEX = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
GENERIC_TAG_REGEX = re.compile(r"<\s*(/?\s*(script|iframe|embed|object|applet|meta|link|style))\b[^>]*>", re.IGNORECASE)
EVENT_HANDLER_REGEX = re.compile(r"\bon\w+\s*=\s*['\"][^'\"]*['\"]", re.IGNORECASE)
JS_PROTOCOL_REGEX = re.compile(r"\bjavascript:\s*", re.IGNORECASE)
DATA_HTML_REGEX = re.compile(r"\bdata:text/html\s*", re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """
    Sanitizes string inputs to prevent Stored & Reflected Cross-Site Scripting (XSS).
    Strips executable scripts, dangerous HTML tags, and inline JavaScript event handlers.
    """
    if not isinstance(text, str):
        return text

    # Strip script blocks
    cleaned = SCRIPT_TAG_REGEX.sub("", text)
    # Strip dangerous HTML tags
    cleaned = GENERIC_TAG_REGEX.sub("", cleaned)
    # Strip javascript: pseudo-protocol
    cleaned = JS_PROTOCOL_REGEX.sub("", cleaned)
    # Strip data:text/html
    cleaned = DATA_HTML_REGEX.sub("", cleaned)
    # Strip inline event handlers like onerror="alert(1)"
    cleaned = EVENT_HANDLER_REGEX.sub("", cleaned)

    return cleaned


def sanitize_payload(data: Any) -> Any:
    """
    Recursively sanitizes dictionary, list, or string data structures.
    """
    if isinstance(data, dict):
        return {k: sanitize_payload(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    elif isinstance(data, str):
        return sanitize_text(data)
    return data


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware for incoming payload sanitization.
    Intercepts POST, PUT, and PATCH JSON bodies to strip malicious XSS payloads.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        raw_data = json.loads(body_bytes.decode("utf-8"))
                        sanitized_data = sanitize_payload(raw_data)
                        sanitized_bytes = json.dumps(sanitized_data).encode("utf-8")

                        # Replace request receive callable to feed sanitized bytes
                        async def receive():
                            return {"type": "http.request", "body": sanitized_bytes, "more_body": False}

                        request._receive = receive
                except Exception:
                    # In case of malformed JSON or streaming body, let normal request handling proceed
                    pass

        return await call_next(request)
