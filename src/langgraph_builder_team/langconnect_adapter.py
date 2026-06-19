from __future__ import annotations

from typing import Any

import httpx

from .models import LangConnectQueryRequest
from .settings import get_settings


class LangConnectUnavailable(RuntimeError):
    pass


def langconnect_status() -> dict[str, object]:
    settings = get_settings()
    return {
        "implemented": True,
        "mode": "external RAG backend adapter",
        "configured": bool(settings.langconnect_url),
        "url": settings.langconnect_url,
        "fallback": "qdrant",
    }


def query_langconnect(payload: LangConnectQueryRequest) -> dict[str, Any]:
    settings = get_settings()
    if not settings.langconnect_url:
        raise LangConnectUnavailable("LANGCONNECT_URL is not configured")
    response = httpx.post(
        f"{settings.langconnect_url.rstrip('/')}/query",
        json=payload.model_dump(mode="json"),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
