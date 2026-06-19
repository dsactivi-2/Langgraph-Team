from __future__ import annotations

from textwrap import dedent
from typing import Any

from .models import OpenSWETaskRequest
from .settings import get_settings


def _import_deepagents():
    try:
        from deepagents import create_deep_agent

        return create_deep_agent
    except Exception:
        return None


def deep_agents_status() -> dict[str, object]:
    return {
        "implemented": True,
        "runtime": "python",
        "installed": _import_deepagents() is not None,
        "mode": "starter-code + optional runtime factory",
    }


def deep_agents_code() -> str:
    return dedent(
        """
        from deepagents import create_deep_agent

        from langgraph_builder_team.langchain_adapter import build_builder_tool


        SYSTEM_PROMPT = \"\"\"You are a production LangGraph builder.
        Plan, implement, test, review, and package generated projects.
        Use memory and MCP tools when available. Ask for approval before deployment.
        \"\"\"


        def create_builder_deep_agent(model):
            return create_deep_agent(
                model=model,
                tools=[build_builder_tool()],
                system_prompt=SYSTEM_PROMPT,
            )
        """
    ).strip()


def deep_agents_js_code() -> str:
    return dedent(
        """
        import { createDeepAgent } from "deepagents";
        import { DynamicStructuredTool } from "@langchain/core/tools";
        import { z } from "zod";

        const builderTool = new DynamicStructuredTool({
          name: "langgraph_builder_team",
          description: "Build and verify LangGraph projects through the Python backend.",
          schema: z.object({
            user_request: z.string(),
            project_id: z.string().optional()
          }),
          func: async (input) => {
            const response = await fetch(`${process.env.BUILDER_API_URL}/build`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(input)
            });
            if (!response.ok) throw new Error(await response.text());
            return JSON.stringify(await response.json());
          }
        });

        export function createBuilderDeepAgent(model) {
          return createDeepAgent({
            model,
            tools: [builderTool],
            systemPrompt: "You are a production LangGraph builder with memory and review gates."
          });
        }
        """
    ).strip()


def open_swe_task_payload(payload: OpenSWETaskRequest) -> dict[str, Any]:
    settings = get_settings()
    return {
        "target": settings.open_swe_url or "external-open-swe",
        "task": {
            "title": payload.title,
            "description": payload.description,
            "repository": payload.repository,
            "branch": payload.branch,
            "labels": payload.labels,
            "source": "langgraph-builder-team",
        },
        "handoff": {
            "recommended_agent": "Open SWE",
            "expected_outputs": ["branch", "pull_request", "test_report"],
        },
    }


def open_swe_status() -> dict[str, object]:
    settings = get_settings()
    return {
        "implemented": True,
        "mode": "task payload adapter",
        "url_configured": bool(settings.open_swe_url),
        "url": settings.open_swe_url,
    }
