import asyncio
import json
import logging
import aio_pika
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [Consumer] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("s247.worker.consumer")


async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        try:
            body = message.body.decode("utf-8")
            data = json.loads(body)
            routing_key = message.routing_key
            logger.info("Processed message [routing_key=%s]: %s", routing_key, data)
        except Exception as e:
            logger.error("Error processing incoming message: %s", e)


async def main():
    logger.info("Starting RabbitMQ consumer worker for s247...")
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)

                # Listen to core queues in the central hub vhost
                for queue_name in ["q.events", "q.telemetry", "q.sync.in"]:
                    try:
                        queue = await channel.get_queue(queue_name)
                        await queue.consume(process_message)
                        logger.info("Consumer bound to queue: %s", queue_name)
                    except Exception as q_err:
                        logger.warning("Queue %s not available yet: %s", queue_name, q_err)

                logger.info("s247 consumer waiting for AMQP messages...")
                await asyncio.Future()  # Keep worker alive
        except Exception as e:
            logger.warning("Connection lost to RabbitMQ broker: %s. Retrying in 5s...", e)
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
