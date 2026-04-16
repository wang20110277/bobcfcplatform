import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MQProducer:
    """RocketMQ message producer wrapper."""

    def __init__(self, namesrv: str):
        self._namesrv = namesrv
        self._producer = None

    async def start(self):
        try:
            from rocketmq.client import Producer
            self._producer = Producer(self._namesrv)
            self._producer.start()
            logger.info("RocketMQ producer started")
        except Exception as e:
            logger.warning(f"RocketMQ producer failed to start: {e}")
            self._producer = None

    async def send(self, topic: str, message: dict, delay_level: int = 0):
        if self._producer is None:
            logger.warning(f"RocketMQ producer not available, skipping message to {topic}")
            return

        try:
            from rocketmq.message import Message as RMQMessage
            body = json.dumps(message).encode("utf-8")
            msg = RMQMessage(topic, body)
            if delay_level > 0:
                msg.delay_time_level = delay_level
            result = self._producer.send_sync(msg)
            logger.info(f"Sent to {topic}: {result}")
        except Exception as e:
            logger.error(f"Failed to send to {topic}: {e}")

    async def stop(self):
        if self._producer:
            try:
                self._producer.shutdown()
            except Exception:
                pass
            self._producer = None


# Global producer instance
mq_producer: MQProducer | None = None


async def init_mq(namesrv: str) -> MQProducer:
    global mq_producer
    mq_producer = MQProducer(namesrv)
    await mq_producer.start()
    return mq_producer


async def close_mq():
    global mq_producer
    if mq_producer:
        await mq_producer.stop()
        mq_producer = None
