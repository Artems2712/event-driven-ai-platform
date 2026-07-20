# Event-Driven AI Platform

Backend architecture project for asynchronous document processing and AI generation.

This repository demonstrates the platform engineering side of AI/LLM systems: API gateway, ingestion jobs, outbox/inbox, idempotency keys, retries, dead-letter queue, worker boundaries, tracing metadata, and integration-testable event flow.

## What This Demonstrates

- FastAPI API gateway for document ingestion jobs.
- Event-driven pipeline for document parsing, embedding, retrieval indexing, generation and notification.
- Outbox pattern for transactional event publishing.
- Inbox/idempotency pattern for exactly-once-ish worker behavior.
- Retry policy and dead-letter queue.
- PostgreSQL, Redis, RabbitMQ and Qdrant in Docker Compose.
- Worker modules that can be moved to Celery, Dramatiq or ARQ.
- pytest, Ruff, mypy and GitHub Actions.

## Architecture

```text
API Gateway
  -> creates ingestion job
  -> writes outbox event
  -> dispatcher publishes to RabbitMQ
  -> document worker parses text
  -> embedding worker indexes vectors in Qdrant
  -> generation worker creates answer draft
  -> notification worker emits WebSocket/SSE status
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn ai_platform.api.main:app --reload
```

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

RAG and agents are only part of production AI engineering. A real backend also needs asynchronous ingestion, delivery guarantees, idempotent workers, retries, observability, and failure handling. This project is shaped to make those backend architecture skills visible.
