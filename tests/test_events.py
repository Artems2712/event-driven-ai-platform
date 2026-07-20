from ai_platform.events.contracts import Event
from ai_platform.events.outbox import InMemoryBroker, Outbox, OutboxDispatcher


def test_outbox_dispatches_pending_events_once() -> None:
    outbox = Outbox()
    broker = InMemoryBroker()
    dispatcher = OutboxDispatcher(outbox=outbox, broker=broker)
    event = Event(
        type="document.ingest.requested",
        payload={"document_id": "doc-1", "text": "hello"},
        idempotency_key="doc-1",
    )

    outbox.add(event)

    assert dispatcher.dispatch_once() == 1
    assert dispatcher.dispatch_once() == 0
    assert broker.messages == [event]
