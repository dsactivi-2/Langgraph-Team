from langgraph_builder_team.graph import run_build
from langgraph_builder_team.models import AgentStatus


def test_run_build_completes_with_artifacts():
    state = run_build("Build a LangGraph project", project_id="test-project")

    assert state.status == AgentStatus.COMPLETED
    assert state.quality_score >= 75
    assert state.plan
    assert state.generated_artifacts
    assert state.deployment_instructions
    assert all(feedback.severity != "critical" for feedback in state.review_feedback)


def test_run_build_rejects_blank_request():
    try:
        run_build("   ")
    except ValueError as error:
        assert "user_request" in str(error)
    else:
        raise AssertionError("blank request should fail")
