import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

JobStatus = Literal["queued", "parsing", "embedding", "generating", "completed", "failed"]


@dataclass
class IngestionJob:
    document_id: str
    status: JobStatus = "queued"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str | None = None
    progress: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def advance(self, status: JobStatus, progress: int) -> None:
        self.status = status
        self.progress = progress
        self.updated_at = datetime.now(UTC)


class JobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, IngestionJob] = {}

    def create(self, document_id: str, idempotency_key: str | None = None) -> IngestionJob:
        job = IngestionJob(document_id=document_id, idempotency_key=idempotency_key)
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> IngestionJob | None:
        return self.jobs.get(job_id)
