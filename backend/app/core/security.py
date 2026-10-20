import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import jwt, JWTError
from app.core.config import settings


import re


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validates password strength according to healthcare application standards:
    - Minimum 6 characters (recommended 8+)
    - Maximum 128 characters to prevent bcrypt DoS
    """
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters"
    return True, None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if not plain_password or not hashed_password:
            return False
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    # Use standard 12 rounds for balanced security & performance
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def get_client_ip(request: Any) -> str:
    """
    Extracts the client IP safely from trusted proxy headers or socket address.
    Priority order:
    1. Render-Proxy-Client-IP: Set exclusively by Render's edge proxy; cannot be spoofed by clients.
    2. CF-Connecting-IP: Set by Cloudflare's edge proxy.
    3. True-Client-IP: Set by enterprise CDNs/Cloudflare.
    4. X-Real-IP: Set by upstream reverse proxy.
    5. X-Forwarded-For: Leftmost client IP if available.
    6. Direct socket host (request.client.host).
    """
    if not request:
        return "127.0.0.1"
    headers = getattr(request, "headers", {})
    # 1. Render proxy unforgeable header
    render_ip = headers.get("Render-Proxy-Client-IP") or headers.get("render-proxy-client-ip")
    if render_ip and render_ip.strip():
        return render_ip.strip()
    # 2. Cloudflare unforgeable header
    cf_ip = headers.get("CF-Connecting-IP") or headers.get("cf-connecting-ip")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()
    # 3. True-Client-IP
    true_ip = headers.get("True-Client-IP") or headers.get("true-client-ip")
    if true_ip and true_ip.strip():
        return true_ip.strip()
    # 4. Upstream single-hop proxy
    real_ip = headers.get("X-Real-IP") or headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    # 5. X-Forwarded-For
    forwarded = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    if forwarded and forwarded.strip():
        return forwarded.split(",")[0].strip()
    # 6. Direct socket peer
    client = getattr(request, "client", None)
    if client and getattr(client, "host", None):
        return client.host
    return "127.0.0.1"


def get_client_user_agent(request: Any) -> Optional[str]:
    """
    Extracts the User-Agent safely from request headers, truncated to 255 chars.
    """
    if not request:
        return None
    headers = getattr(request, "headers", {})
    ua = headers.get("User-Agent") or headers.get("user-agent")
    return ua[:255] if ua else None
