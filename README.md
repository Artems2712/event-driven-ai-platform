# Event-Driven AI Platform

Reference implementation of event-driven AI backend patterns.

The default API uses in-memory adapters so the project is fast to inspect and deterministic in CI. The repository also includes production adapter code for PostgreSQL job/outbox persistence, RabbitMQ event publishing, and Qdrant document indexing.

## What This Demonstrates

- FastAPI gateway for document ingestion jobs.
- In-memory reference flow for jobs, outbox, broker, idempotency, retries, and workers.
- PostgreSQL repository that stores an ingestion job and outbox event in one transaction.
- RabbitMQ publisher built with `aio-pika`.
- Qdrant indexer with deterministic hashing vectors for document text.
- Production pipeline wiring:

```text
POST /documents
-> PostgreSQL transaction: job + outbox row
-> dispatcher publishes outbox events through RabbitMQ
-> document worker parses text
-> Qdrant upsert stores indexed document text
-> PostgreSQL status update marks progress/completion
```

- Docker Compose topology for PostgreSQL, Redis, RabbitMQ, and Qdrant.
- pytest, Ruff, mypy, and GitHub Actions.

## Architecture

```text
API Gateway
  -> creates ingestion job
  -> writes outbox event
  -> dispatcher publishes event
  -> document worker processes text
  -> vector indexer writes to Qdrant
  -> job status is updated
```

The in-memory implementation is intentionally small and easy to test. The production adapter classes are separated so they can be wired into a worker process without changing event contracts or worker behavior.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn ai_platform.api.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
uvicorn ai_platform.api.main:app --reload
```

## Production Adapters

Install runtime dependencies:

```bash
pip install -e ".[runtime]"
```

Adapter modules:

- `ai_platform.storage.postgres.PostgresJobOutboxRepository`
- `ai_platform.events.rabbitmq.RabbitMQBroker`
- `ai_platform.vector.qdrant.QdrantDocumentIndexer`
- `ai_platform.runtime.production.ProductionIngestionPipeline`

These classes provide the real external integration path while CI keeps using fake/in-memory adapters.

## Docker Compose

```bash
docker compose up --build
```

Services included:

- API service;
- PostgreSQL;
- Redis;
- RabbitMQ;
- Qdrant.

## Why This Exists

RAG and agents are only part of production AI engineering. A real backend also needs asynchronous ingestion, delivery guarantees, idempotent workers, retries, observability, and failure handling. This project is shaped to make those backend architecture skills visible without pretending every infrastructure component is enabled in the default local API.
