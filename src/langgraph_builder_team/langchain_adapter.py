from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool

from .graph import run_build


def run_builder_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the builder workflow through a LangChain-compatible callable."""
    state = run_build(
        str(payload["user_request"]),
        payload.get("project_id"),
    )
    return state.model_dump(mode="json")


def build_builder_runnable() -> RunnableLambda:
    return RunnableLambda(run_builder_payload)


def _builder_tool(user_request: str, project_id: str | None = None) -> dict[str, Any]:
    return run_builder_payload({"user_request": user_request, "project_id": project_id})


def build_builder_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=_builder_tool,
        name="langgraph_builder_team",
        description="Plan, build, test, review, verify, and package a LangGraph project.",
    )


def langchain_status() -> dict[str, object]:
    return {
        "implemented": True,
        "runtime": "python",
        "adapter": "RunnableLambda + StructuredTool",
        "entrypoints": ["build_builder_runnable", "build_builder_tool"],
    }
