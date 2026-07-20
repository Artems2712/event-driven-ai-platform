import os
import uuid

import pytest

from ai_platform.events.rabbitmq import RabbitMQBroker
from ai_platform.events.serialization import event_from_json
from ai_platform.runtime.production import ProductionIngestionPipeline
from ai_platform.storage.postgres import PostgresJobOutboxRepository
from ai_platform.vector.qdrant import QdrantDocumentIndexer

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_postgres_rabbitmq_qdrant_integration_path() -> None:
    if os.getenv("RUN_INTEGRATION") != "true":
        pytest.skip("Set RUN_INTEGRATION=true and service URLs to run external adapter tests.")

    postgres_dsn = _required_env("POSTGRES_DSN")
    rabbitmq_url = _required_env("RABBITMQ_URL")
    qdrant_url = _required_env("QDRANT_URL")
    idempotency_key = f"integration-{uuid.uuid4()}"
    queue_name = f"document.ingest.requested.{uuid.uuid4().hex}"
    collection_name = f"ai_documents_{uuid.uuid4().hex}"

    repository = await PostgresJobOutboxRepository.connect(postgres_dsn)
    try:
        await repository.init_schema()
        broker = RabbitMQBroker(rabbitmq_url, queue_name=queue_name)
        indexer = QdrantDocumentIndexer(qdrant_url, collection_name=collection_name)
        pipeline = ProductionIngestionPipeline(
            repository=repository,
            broker=broker,
            indexer=indexer,
        )

        first_job = await pipeline.create_document(
            document_id="doc-integration",
            text="external integration path with durable outbox",
            idempotency_key=idempotency_key,
        )
        second_job = await pipeline.create_document(
            document_id="doc-integration",
            text="duplicate request should reuse the original job",
            idempotency_key=idempotency_key,
        )
        pending = [
            event
            for event in await repository.pending_events(limit=100)
            if event.idempotency_key == idempotency_key
        ]

        assert second_job.id == first_job.id
        assert len(pending) == 1

        await broker.publish(pending[0])
        received = event_from_json(await _read_one_rabbitmq_message(rabbitmq_url, queue_name))
        await repository.mark_published(pending[0].event_id)
        vector_id = await pipeline.process_document_event(pending[0])
        stored_job = await repository.get(first_job.id)

        assert received.idempotency_key == idempotency_key
        assert vector_id is not None
        assert stored_job is not None
        assert stored_job.status == "completed"
        assert stored_job.progress == 100
    finally:
        await repository.pool.close()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required for integration tests.")
    return value


async def _read_one_rabbitmq_message(url: str, queue_name: str) -> str:
    import aio_pika

    connection = await aio_pika.connect_robust(url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        message = await queue.get(timeout=5, fail=False)
        assert message is not None
        async with message.process():
            return message.body.decode("utf-8")
