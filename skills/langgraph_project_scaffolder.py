from __future__ import annotations

from typing import Any

from langgraph_builder_team.graph import run_build


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Run the LangGraph project scaffolder skill.

    The function shape is intentionally simple so Hermes-style runtimes can call
    it as a tool while the canonical implementation remains in the application
    package.
    """
    user_request = input_data["user_request"]
    project_id = input_data.get("project_id")
    state = run_build(user_request=user_request, project_id=project_id)
    return {
        "project_id": state.project_id,
        "status": str(state.status),
        "quality_score": state.quality_score,
        "artifacts": [
            {
                "filename": artifact.filename,
                "artifact_type": artifact.artifact_type,
                "description": artifact.description,
            }
            for artifact in state.generated_artifacts
        ],
        "deployment_instructions": state.deployment_instructions,
        "recommended_next_steps": state.recommended_next_steps,
    }
