from fastapi.testclient import TestClient

from langgraph_builder_team.api import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_build_endpoint():
    client = TestClient(app)

    response = client.post("/build", json={"user_request": "Build a LangGraph test project"})

    assert response.status_code == 200
    body = response.json()
    assert body["quality_score"] >= 75
    assert body["artifacts"]

    history_response = client.get("/builds")
    assert history_response.status_code == 200
    assert any(item["project_id"] == body["project_id"] for item in history_response.json())


def test_build_endpoint_rejects_empty_request():
    client = TestClient(app)

    response = client.post("/build", json={"user_request": ""})

    assert response.status_code == 422


def test_metadata_endpoint_hides_secret_values():
    client = TestClient(app)

    response = client.get("/metadata")

    assert response.status_code == 200
    body = response.json()
    assert "secrets" in body
    assert "openai_api_key_set" in body["secrets"]
    assert "sk-" not in str(body)
    assert "llm" in body
    assert "auth" in body


def test_agents_and_templates_endpoints():
    client = TestClient(app)

    agents_response = client.get("/agents")
    templates_response = client.get("/templates")

    assert agents_response.status_code == 200
    assert templates_response.status_code == 200
    assert agents_response.json()["agents"]
    assert templates_response.json()["templates"]


def test_chat_endpoints_persist_or_fallback():
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"project_id": "test-chat", "role": "user", "content": "Remember this plan"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"]["project_id"] == "test-chat"

    history_response = client.get("/chat/test-chat")
    assert history_response.status_code == 200
    assert history_response.json()["messages"]


def test_memory_upsert_and_search():
    client = TestClient(app)

    upsert_response = client.post(
        "/memory/upsert",
        json={
            "project_id": "test-memory",
            "text": "Postgres checkpointer and Qdrant search",
            "metadata": {"kind": "test"},
        },
    )
    assert upsert_response.status_code == 200
    assert upsert_response.json()["id"]

    search_response = client.post(
        "/memory/search",
        json={"project_id": "test-memory", "query": "Qdrant search", "limit": 3},
    )
    assert search_response.status_code == 200
    assert "results" in search_response.json()


def test_llm_completion_requires_configuration():
    client = TestClient(app)

    response = client.post("/llm/complete", json={"prompt": "Hello"})

    assert response.status_code in {200, 503}


def test_auth_status_endpoint():
    client = TestClient(app)

    response = client.get("/auth/status")

    assert response.status_code == 200
    assert response.json()["auth_enabled"] is False


def test_integrations_endpoint_reports_missing_points_as_implemented_adapters():
    client = TestClient(app)

    response = client.get("/integrations")

    assert response.status_code == 200
    integrations = response.json()["integrations"]
    for name in [
        "langchain",
        "langchain_js",
        "langgraph",
        "langgraph_js",
        "deep_agents",
        "deep_agents_js",
        "deep_agents_code",
        "open_swe",
        "mcp_adapters",
        "agent_protocol",
        "langconnect",
    ]:
        assert integrations[name]["implemented"] is True


def test_agent_protocol_thread_and_run():
    client = TestClient(app)

    thread_response = client.post(
        "/agent-protocol/threads",
        json={"thread_id": "agent-protocol-test"},
    )
    assert thread_response.status_code == 200
    assert thread_response.json()["thread_id"] == "agent-protocol-test"

    run_response = client.post(
        "/agent-protocol/runs",
        json={
            "thread_id": "agent-protocol-test",
            "input": "Build through Agent Protocol",
        },
    )
    assert run_response.status_code == 200
    assert run_response.json()["project_id"] == "agent-protocol-test"


def test_mcp_and_deep_agents_code_endpoints():
    client = TestClient(app)

    mcp_response = client.get("/mcp/tools")
    assert mcp_response.status_code == 200
    assert mcp_response.json()["tools"] == []

    code_response = client.get("/integrations/deep-agents/code")
    assert code_response.status_code == 200
    assert "create_deep_agent" in code_response.json()["content"]


def test_open_swe_task_payload_endpoint():
    client = TestClient(app)

    response = client.post(
        "/integrations/open-swe/task",
        json={"title": "Fix tests", "description": "Run tests and fix failures."},
    )

    assert response.status_code == 200
    assert response.json()["task"]["title"] == "Fix tests"


def test_langconnect_endpoint_requires_configuration():
    client = TestClient(app)

    response = client.post(
        "/integrations/langconnect/query",
        json={"query": "deployment memory", "project_id": "test-memory"},
    )

    assert response.status_code == 503
