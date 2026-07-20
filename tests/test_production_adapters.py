import pytest

from ai_platform.events.contracts import Event
from ai_platform.events.serialization import event_from_json, event_to_json
from ai_platform.runtime.production import ProductionIngestionPipeline
from ai_platform.storage.jobs import IngestionJob
from ai_platform.vector.qdrant import hashing_vector


def test_event_json_roundtrip() -> None:
    event = Event(
        type="document.ingest.requested",
        payload={"document_id": "doc-1", "text": "hello"},
        idempotency_key="doc-1",
    )

    restored = event_from_json(event_to_json(event))

    assert restored.event_id == event.event_id
    assert restored.type == event.type
    assert restored.payload == event.payload


def test_hashing_vector_is_normalized_and_stable() -> None:
    first = hashing_vector("hello production qdrant", dimensions=8)
    second = hashing_vector("hello production qdrant", dimensions=8)

    assert first == second
    assert len(first) == 8
    assert sum(value * value for value in first) == pytest.approx(1.0)


@pytest.mark.anyio
async def test_production_pipeline_persists_outbox_dispatches_and_indexes() -> None:
    repository = FakeRepository()
    broker = FakeBroker()
    indexer = FakeIndexer()
    pipeline = ProductionIngestionPipeline(
        repository=repository,
        broker=broker,
        indexer=indexer,
    )

    job = await pipeline.create_document(
        document_id="doc-1",
        text="hello from production path",
        idempotency_key="doc-1",
    )
    dispatched = await pipeline.dispatch_once()
    vector_id = await pipeline.process_document_event(broker.events[0])

    assert job.document_id == "doc-1"
    assert dispatched == 1
    assert repository.published == [broker.events[0].event_id]
    assert vector_id == "vec-doc-1"
    assert indexer.documents == [("doc-1", "hello from production path")]
    assert repository.status_updates[-1] == (job.id, "completed", 100)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeRepository:
    def __init__(self) -> None:
        self.jobs: list[IngestionJob] = []
        self.events: list[Event] = []
        self.published: list[str] = []
        self.status_updates: list[tuple[str, str, int]] = []

    async def insert_job_and_event(self, job: IngestionJob, event: Event) -> IngestionJob:
        self.jobs.append(job)
        self.events.append(event)
        return job

    async def pending_events(self, limit: int = 100) -> list[Event]:
        return self.events[:limit]

    async def mark_published(self, event_id: str) -> None:
        self.published.append(event_id)

    async def update_status(self, job_id: str, status: str, progress: int) -> None:
        self.status_updates.append((job_id, status, progress))


class FakeBroker:
    def __init__(self) -> None:
        self.events: list[Event] = []

    async def publish(self, event: Event) -> None:
        self.events.append(event)


class FakeIndexer:
    def __init__(self) -> None:
        self.documents: list[tuple[str, str]] = []

    async def upsert_document(self, document_id: str, text: str) -> str:
        self.documents.append((document_id, text))
        return f"vec-{document_id}"
