from fastapi.testclient import TestClient

from forgeloop.api.app import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_create_mock_task():
    r = client.post(
        "/api/tasks",
        json={"goal": "create a file", "use_mock": True, "max_steps": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in {"succeeded", "running", "step_limit", "failed"}
    # mock script should finish
    assert data["status"] == "succeeded"
    assert data["result"]["steps"]


def test_creds_status():
    r = client.get("/api/creds")
    assert r.status_code == 200
    assert "configured" in r.json()
