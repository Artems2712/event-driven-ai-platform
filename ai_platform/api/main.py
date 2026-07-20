from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_platform.events.contracts import Event
from ai_platform.events.outbox import InMemoryBroker, Outbox, OutboxDispatcher
from ai_platform.storage.jobs import JobRepository

app = FastAPI(title="Event-Driven AI Platform", version="0.1.0")
jobs = JobRepository()
outbox = Outbox()
broker = InMemoryBroker()
dispatcher = OutboxDispatcher(outbox=outbox, broker=broker)


class DocumentRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=1)


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/documents", response_model=JobResponse)
def create_document(request: DocumentRequest) -> JobResponse:
    job = jobs.create(document_id=request.document_id)
    outbox.add(
        Event(
            type="document.ingest.requested",
            payload={"document_id": request.document_id, "text": request.text},
            idempotency_key=request.idempotency_key,
        )
    )
    return JobResponse(job_id=job.id, status=job.status, progress=job.progress)


@app.post("/dispatch")
def dispatch() -> dict[str, int]:
    return {"published": dispatcher.dispatch_once()}


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job.id, status=job.status, progress=job.progress)
