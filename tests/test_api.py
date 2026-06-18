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


def test_build_endpoint_rejects_empty_request():
    client = TestClient(app)

    response = client.post("/build", json={"user_request": ""})

    assert response.status_code == 422
