from ai_platform.events.contracts import Event
from ai_platform.workers.base import Worker


class DocumentWorker(Worker):
    def process(self, event: Event) -> Event:
        text = event.payload["text"].strip()
        if not text:
            raise ValueError("document text is empty")
        return Event(
            type="document.parsed",
            payload={
                "document_id": event.payload["document_id"],
                "text": text,
            },
            idempotency_key=f"parsed:{event.payload['document_id']}",
            trace_id=event.trace_id,
        )
