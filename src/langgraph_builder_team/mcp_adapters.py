from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from .settings import get_settings


class MCPServerDefinition(BaseModel):
    name: str = Field(..., min_length=1)
    transport: str = Field(default="stdio")
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)


def _import_client():
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        return MultiServerMCPClient
    except Exception:
        return None


def parse_mcp_servers(raw: str | None = None) -> list[MCPServerDefinition]:
    source = raw if raw is not None else get_settings().mcp_servers_json
    if not source:
        return []
    try:
        data = json.loads(source)
    except json.JSONDecodeError as exc:
        raise ValueError(f"MCP_SERVERS_JSON is invalid JSON: {exc}") from exc
    if isinstance(data, dict):
        data = [
            {"name": name, **config}
            for name, config in data.items()
            if isinstance(config, dict)
        ]
    try:
        return [MCPServerDefinition.model_validate(item) for item in data]
    except ValidationError as exc:
        raise ValueError(f"MCP server config is invalid: {exc}") from exc


def build_mcp_client_config(servers: list[MCPServerDefinition]) -> dict[str, dict[str, Any]]:
    config: dict[str, dict[str, Any]] = {}
    for server in servers:
        item: dict[str, Any] = {"transport": server.transport}
        if server.command:
            item["command"] = server.command
        if server.args:
            item["args"] = server.args
        if server.url:
            item["url"] = server.url
        if server.headers:
            item["headers"] = server.headers
        config[server.name] = item
    return config


async def list_mcp_tools() -> list[dict[str, Any]]:
    servers = parse_mcp_servers()
    if not servers:
        return []
    client_cls = _import_client()
    if client_cls is None:
        raise RuntimeError("langchain-mcp-adapters is not installed")
    client = client_cls(build_mcp_client_config(servers))
    tools = await client.get_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "args_schema": getattr(tool, "args_schema", None).__name__
            if getattr(tool, "args_schema", None)
            else None,
        }
        for tool in tools
    ]


def mcp_status() -> dict[str, object]:
    servers = parse_mcp_servers()
    return {
        "implemented": True,
        "adapter": "langchain-mcp-adapters",
        "installed": _import_client() is not None,
        "servers_configured": len(servers),
        "server_names": [server.name for server in servers],
    }
