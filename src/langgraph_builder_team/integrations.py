from __future__ import annotations

from pathlib import Path
from typing import Any

from .deep_agents_adapter import deep_agents_status, open_swe_status
from .langchain_adapter import langchain_status
from .langconnect_adapter import langconnect_status
from .mcp_adapters import mcp_status
from .settings import get_settings

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _exists(path: str) -> bool:
    return any((base / path).exists() for base in (Path.cwd(), PACKAGE_ROOT))


def integration_matrix() -> dict[str, dict[str, Any]]:
    settings = get_settings()
    return {
        "langchain": langchain_status(),
        "langchain_js": {
            "implemented": _exists("js-adapters/package.json"),
            "runtime": "node",
            "path": "js-adapters/",
        },
        "langgraph": {
            "implemented": True,
            "runtime": "python",
            "adapter": "StateGraph + PostgresSaver",
            "langgraph_json": _exists("langgraph.json"),
        },
        "langgraph_js": {
            "implemented": _exists("js-adapters/src/langgraph.ts"),
            "runtime": "node",
            "path": "js-adapters/src/langgraph.ts",
        },
        "deep_agents": deep_agents_status(),
        "deep_agents_js": {
            "implemented": _exists("js-adapters/src/deep-agents.ts"),
            "runtime": "node",
            "path": "js-adapters/src/deep-agents.ts",
        },
        "deep_agents_code": {
            "implemented": True,
            "runtime": "python + node",
            "endpoints": ["/integrations/deep-agents/code", "/integrations/deep-agents/js-code"],
        },
        "open_swe": open_swe_status(),
        "mcp_adapters": mcp_status(),
        "agent_protocol": {
            "implemented": settings.agent_protocol_enabled,
            "mode": "FastAPI compatible thread/run surface",
            "endpoints": [
                "/agent-protocol/info",
                "/agent-protocol/threads",
                "/agent-protocol/runs",
            ],
        },
        "langsmith": {
            "implemented": True,
            "mode": "env-driven tracing + metadata",
            "configured": bool(settings.langsmith_api_key),
            "project": settings.langsmith_project,
            "tracing_enabled": settings.langchain_tracing_v2,
        },
        "langconnect": langconnect_status(),
    }
