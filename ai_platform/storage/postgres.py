from typing import Any

from ai_platform.events.contracts import Event
from ai_platform.events.serialization import event_from_dict, event_to_dict
from ai_platform.storage.jobs import IngestionJob, JobStatus


class PostgresJobOutboxRepository:
    def __init__(self, pool: Any) -> None:
        self.pool = pool

    @classmethod
    async def connect(cls, dsn: str) -> "PostgresJobOutboxRepository":
        import asyncpg

        return cls(await asyncpg.create_pool(dsn))

    async def init_schema(self) -> None:
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                create table if not exists ingestion_jobs (
                  id text primary key,
                  document_id text not null,
                  status text not null,
                  progress integer not null,
                  updated_at timestamptz not null
                );
                create table if not exists outbox_events (
                  event_id text primary key,
                  event_type text not null,
                  payload jsonb not null,
                  idempotency_key text not null unique,
                  trace_id text not null,
                  created_at timestamptz not null,
                  published_at timestamptz
                );
                """
            )

    async def insert_job_and_event(self, job: IngestionJob, event: Event) -> IngestionJob:
        record = event_to_dict(event)
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                    insert into ingestion_jobs (id, document_id, status, progress, updated_at)
                    values ($1, $2, $3, $4, $5)
                    on conflict (id) do nothing
                    """,
                    job.id,
                    job.document_id,
                    job.status,
                    job.progress,
                    job.updated_at,
                )
                await connection.execute(
                    """
                    insert into outbox_events (
                      event_id, event_type, payload, idempotency_key, trace_id, created_at
                    )
                    values ($1, $2, $3::jsonb, $4, $5, $6)
                    on conflict (idempotency_key) do nothing
                    """,
                    event.event_id,
                    event.type,
                    record["payload"],
                    event.idempotency_key,
                    event.trace_id,
                    event.created_at,
                )
        return job

    async def get(self, job_id: str) -> IngestionJob | None:
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                select id, document_id, status, progress, updated_at
                from ingestion_jobs
                where id = $1
                """,
                job_id,
            )
        if row is None:
            return None
        return IngestionJob(
            id=str(row["id"]),
            document_id=str(row["document_id"]),
            status=row["status"],
            progress=int(row["progress"]),
            updated_at=row["updated_at"],
        )

    async def update_status(self, job_id: str, status: JobStatus, progress: int) -> None:
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                update ingestion_jobs
                set status = $2, progress = $3, updated_at = now()
                where id = $1
                """,
                job_id,
                status,
                progress,
            )

    async def pending_events(self, limit: int = 100) -> list[Event]:
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                """
                select event_id, event_type, payload, idempotency_key, trace_id, created_at
                from outbox_events
                where published_at is null
                order by created_at
                limit $1
                """,
                limit,
            )
        return [
            event_from_dict(
                {
                    "event_id": row["event_id"],
                    "type": row["event_type"],
                    "payload": row["payload"],
                    "idempotency_key": row["idempotency_key"],
                    "trace_id": row["trace_id"],
                    "created_at": row["created_at"].isoformat(),
                }
            )
            for row in rows
        ]

    async def mark_published(self, event_id: str) -> None:
        async with self.pool.acquire() as connection:
            await connection.execute(
                "update outbox_events set published_at = now() where event_id = $1",
                event_id,
            )
