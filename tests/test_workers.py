from ai_platform.events.contracts import Event
from ai_platform.workers.document_worker import DocumentWorker
from ai_platform.workers.embedding_worker import EmbeddingWorker
from ai_platform.workers.generation_worker import GenerationWorker


def test_worker_pipeline_preserves_trace_and_idempotency() -> None:
    requested = Event(
        type="document.ingest.requested",
        payload={"document_id": "doc-1", "text": "hello world"},
        idempotency_key="doc-1",
    )
    document_worker = DocumentWorker()
    embedding_worker = EmbeddingWorker()
    generation_worker = GenerationWorker()

    parsed = document_worker.handle(requested)
    duplicate = document_worker.handle(requested)
    assert parsed is not None
    embedded = embedding_worker.handle(parsed)
    assert embedded is not None
    generated = generation_worker.handle(embedded)
    assert generated is not None

    assert duplicate is None
    assert parsed.trace_id == requested.trace_id
    assert embedded.payload["token_count"] == "2"
    assert generated.type == "generation.completed"


def test_worker_sends_failures_to_dead_letter_queue() -> None:
    worker = DocumentWorker()
    event = Event(
        type="document.ingest.requested",
        payload={"document_id": "doc-1", "text": ""},
        idempotency_key="doc-1",
    )

    result = worker.handle(event)

    assert result is None
    assert len(worker.dead_letter_queue.failed_events) == 1
