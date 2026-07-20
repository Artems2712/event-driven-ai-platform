from typing import Protocol

from ai_platform.events.contracts import Event
from ai_platform.storage.jobs import IngestionJob, JobStatus
from ai_platform.workers.document_worker import DocumentWorker


class JobOutboxRepository(Protocol):
    async def insert_job_and_event(self, job: IngestionJob, event: Event) -> IngestionJob:
        """Persist a job and an outbox event in one transaction."""

    async def pending_events(self, limit: int = 100) -> list[Event]:
        """Return unpublished outbox events."""

    async def mark_published(self, event_id: str) -> None:
        """Mark one outbox event as published."""

    async def update_status(self, job_id: str, status: JobStatus, progress: int) -> None:
        """Update job status."""


class AsyncBroker(Protocol):
    async def publish(self, event: Event) -> None:
        """Publish an event to an external queue."""


class DocumentIndexer(Protocol):
    async def upsert_document(self, document_id: str, text: str) -> str:
        """Index parsed text and return an external vector id."""


class ProductionIngestionPipeline:
    def __init__(
        self,
        repository: JobOutboxRepository,
        broker: AsyncBroker,
        indexer: DocumentIndexer,
    ) -> None:
        self.repository = repository
        self.broker = broker
        self.indexer = indexer
        self.document_worker = DocumentWorker()

    async def create_document(
        self,
        document_id: str,
        text: str,
        idempotency_key: str,
    ) -> IngestionJob:
        job = IngestionJob(document_id=document_id, idempotency_key=idempotency_key)
        event = Event(
            type="document.ingest.requested",
            payload={
                "job_id": job.id,
                "document_id": document_id,
                "text": text,
            },
            idempotency_key=idempotency_key,
        )
        return await self.repository.insert_job_and_event(job, event)

    async def dispatch_once(self, limit: int = 100) -> int:
        published = 0
        for event in await self.repository.pending_events(limit=limit):
            await self.broker.publish(event)
            await self.repository.mark_published(event.event_id)
            published += 1
        return published

    async def process_document_event(self, event: Event) -> str | None:
        parsed = self.document_worker.handle(event)
        if parsed is None:
            return None
        job_id = event.payload["job_id"]
        await self.repository.update_status(job_id, "embedding", 50)
        vector_id = await self.indexer.upsert_document(
            document_id=parsed.payload["document_id"],
            text=parsed.payload["text"],
        )
        await self.repository.update_status(job_id, "completed", 100)
        return vector_id
