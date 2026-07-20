import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

EventType = Literal[
    "document.ingest.requested",
    "document.parsed",
    "embedding.created",
    "generation.completed",
    "notification.requested",
]


@dataclass(frozen=True)
class Event:
    type: EventType
    payload: dict[str, str]
    idempotency_key: str
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
