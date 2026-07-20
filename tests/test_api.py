from fastapi.testclient import TestClient

from ai_platform.api.main import app


def test_api_creates_job_and_dispatches_outbox_event() -> None:
    client = TestClient(app)
    response = client.post(
        "/documents",
        json={
            "document_id": "doc-api",
            "text": "hello from api",
            "idempotency_key": "doc-api",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "queued"

    dispatch_response = client.post("/dispatch")
    assert dispatch_response.json()["published"] >= 1

    job_response = client.get(f"/jobs/{payload['job_id']}")
    assert job_response.status_code == 200
