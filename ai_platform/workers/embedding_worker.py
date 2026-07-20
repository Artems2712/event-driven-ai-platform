from ai_platform.events.contracts import Event
from ai_platform.workers.base import Worker


class EmbeddingWorker(Worker):
    def process(self, event: Event) -> Event:
        token_count = len(event.payload["text"].split())
        return Event(
            type="embedding.created",
            payload={
                "document_id": event.payload["document_id"],
                "vector_id": f"vec:{event.payload['document_id']}",
                "token_count": str(token_count),
            },
            idempotency_key=f"embedding:{event.payload['document_id']}",
            trace_id=event.trace_id,
        )
