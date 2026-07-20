from dataclasses import dataclass, field

from ai_platform.events.contracts import Event


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3

    def should_retry(self, attempts: int) -> bool:
        return attempts < self.max_attempts


@dataclass
class DeadLetterQueue:
    failed_events: list[tuple[Event, str]] = field(default_factory=list)

    def push(self, event: Event, reason: str) -> None:
        self.failed_events.append((event, reason))
