import pytest
from httpx import ASGITransport, AsyncClient

from ai_platform.api.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_api_creates_job_and_dispatches_outbox_event() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/documents",
            json={
                "document_id": "doc-api",
                "text": "hello from api",
                "idempotency_key": "doc-api",
            },
        )
        dispatch_response = await client.post("/dispatch")
        job_response = await client.get(f"/jobs/{response.json()['job_id']}")

    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "queued"
    assert dispatch_response.json()["published"] >= 1
    assert job_response.status_code == 200


@pytest.mark.anyio
async def test_api_returns_404_for_unknown_job() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/jobs/missing")

    assert response.status_code == 404
