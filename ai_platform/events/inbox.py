from dataclasses import dataclass, field


@dataclass
class Inbox:
    processed_keys: set[str] = field(default_factory=set)

    def seen(self, idempotency_key: str) -> bool:
        return idempotency_key in self.processed_keys

    def mark_processed(self, idempotency_key: str) -> None:
        self.processed_keys.add(idempotency_key)
