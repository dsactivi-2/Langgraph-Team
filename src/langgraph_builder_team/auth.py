from __future__ import annotations

import base64
import hashlib
import hmac
import time

from fastapi import HTTPException, Request, Response, status

from .settings import get_settings


def _sign(value: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session(username: str, max_age: int = 60 * 60 * 12) -> str:
    settings = get_settings()
    expires = int(time.time()) + max_age
    payload = f"{username}:{expires}"
    signature = _sign(payload, settings.auth_session_secret)
    token = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(token.encode("utf-8")).decode("ascii")


def verify_session(token: str | None) -> bool:
    settings = get_settings()
    if not settings.auth_enabled:
        return True
    if not token:
        return False
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        username, expires_text, signature = decoded.rsplit(":", 2)
        payload = f"{username}:{expires_text}"
        if not hmac.compare_digest(signature, _sign(payload, settings.auth_session_secret)):
            return False
        return username == settings.auth_username and int(expires_text) >= int(time.time())
    except Exception:
        return False


def require_auth(request: Request) -> None:
    settings = get_settings()
    if not verify_session(request.cookies.get(settings.auth_cookie_name)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


def set_auth_cookie(response: Response, username: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.auth_cookie_name,
        create_session(username),
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=60 * 60 * 12,
    )


def clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.auth_cookie_name)
