from ai_platform.events.contracts import Event
from ai_platform.events.serialization import event_to_json


class RabbitMQBroker:
    def __init__(self, url: str, queue_name: str = "document.ingest.requested") -> None:
        self.url = url
        self.queue_name = queue_name

    async def publish(self, event: Event) -> None:
        import aio_pika

        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.queue_name, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=event_to_json(event).encode("utf-8"),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue.name,
            )
