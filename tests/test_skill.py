from skills.langgraph_project_scaffolder import run


def test_langgraph_project_scaffolder_skill_returns_contract():
    result = run(
        {
            "user_request": "Build a production-ready LangGraph project",
            "project_id": "skill-test",
        }
    )

    assert result["project_id"] == "skill-test"
    assert result["status"] == "completed"
    assert result["quality_score"] >= 75
    assert result["artifacts"]
    assert result["deployment_instructions"]
