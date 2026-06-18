from langgraph_builder_team.models import BuilderState


def test_builder_state_defaults_project_id():
    state = BuilderState(user_request="Build a test agent")

    assert state.project_id.startswith("project-")
    assert state.current_agent == "orchestrator"
