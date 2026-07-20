from dataclasses import dataclass, field

from ai_platform.events.contracts import Event


@dataclass
class Outbox:
    events: list[Event] = field(default_factory=list)
    published: set[str] = field(default_factory=set)

    def add(self, event: Event) -> None:
        self.events.append(event)

    def pending(self) -> list[Event]:
        return [event for event in self.events if event.event_id not in self.published]

    def mark_published(self, event: Event) -> None:
        self.published.add(event.event_id)


class InMemoryBroker:
    def __init__(self) -> None:
        self.messages: list[Event] = []

    def publish(self, event: Event) -> None:
        self.messages.append(event)


class OutboxDispatcher:
    def __init__(self, outbox: Outbox, broker: InMemoryBroker) -> None:
        self.outbox = outbox
        self.broker = broker

    def dispatch_once(self) -> int:
        count = 0
        for event in self.outbox.pending():
            self.broker.publish(event)
            self.outbox.mark_published(event)
            count += 1
        return count
