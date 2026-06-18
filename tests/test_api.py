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


def test_agents_and_templates_endpoints():
    client = TestClient(app)

    agents_response = client.get("/agents")
    templates_response = client.get("/templates")

    assert agents_response.status_code == 200
    assert templates_response.status_code == 200
    assert agents_response.json()["agents"]
    assert templates_response.json()["templates"]
