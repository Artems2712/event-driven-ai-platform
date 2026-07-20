import json
from datetime import datetime
from typing import Any, cast

from ai_platform.events.contracts import Event, EventType


def event_to_json(event: Event) -> str:
    return json.dumps(event_to_dict(event), separators=(",", ":"))


def event_from_json(value: str) -> Event:
    return event_from_dict(json.loads(value))


def event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "type": event.type,
        "payload": event.payload,
        "idempotency_key": event.idempotency_key,
        "trace_id": event.trace_id,
        "created_at": event.created_at.isoformat(),
    }


def event_from_dict(value: dict[str, Any]) -> Event:
    return Event(
        event_id=str(value["event_id"]),
        type=cast(EventType, value["type"]),
        payload={str(key): str(item) for key, item in dict(value["payload"]).items()},
        idempotency_key=str(value["idempotency_key"]),
        trace_id=str(value["trace_id"]),
        created_at=datetime.fromisoformat(str(value["created_at"])),
    )
