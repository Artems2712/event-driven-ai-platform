from ai_platform.events.contracts import Event
from ai_platform.events.inbox import Inbox
from ai_platform.events.retry import DeadLetterQueue, RetryPolicy


class Worker:
    def __init__(
        self,
        inbox: Inbox | None = None,
        retry_policy: RetryPolicy | None = None,
        dead_letter_queue: DeadLetterQueue | None = None,
    ) -> None:
        self.inbox = inbox or Inbox()
        self.retry_policy = retry_policy or RetryPolicy()
        self.dead_letter_queue = dead_letter_queue or DeadLetterQueue()

    def handle(self, event: Event) -> Event | None:
        if self.inbox.seen(event.idempotency_key):
            return None
        try:
            result = self.process(event)
        except Exception as exc:
            self.dead_letter_queue.push(event, str(exc))
            return None
        self.inbox.mark_processed(event.idempotency_key)
        return result

    def process(self, event: Event) -> Event:
        raise NotImplementedError
