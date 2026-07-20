from ai_platform.events.contracts import Event
from ai_platform.workers.base import Worker


class GenerationWorker(Worker):
    def process(self, event: Event) -> Event:
        return Event(
            type="generation.completed",
            payload={
                "document_id": event.payload["document_id"],
                "answer_id": f"answer:{event.payload['document_id']}",
            },
            idempotency_key=f"generation:{event.payload['document_id']}",
            trace_id=event.trace_id,
        )
