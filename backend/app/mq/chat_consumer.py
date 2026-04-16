"""RocketMQ consumer for chat messages (WebSocket push mode)."""
import json
import logging
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CHAT_TOPIC = "chat-topic"


async def run_chat_consumer():
    """
    Consumes chat messages from RocketMQ, calls Gemini, pushes result via WebSocket.
    This is designed to run as a separate worker process.

    For now, this is a placeholder that can be enabled when RocketMQ is available.
    The synchronous /api/chat endpoint handles requests directly.
    """
    logger.info("Chat consumer starting (placeholder - requires RocketMQ broker)")
    try:
        from rocketmq.client import PushConsumer
    except ImportError:
        logger.warning("rocketmq-client-python not installed, chat consumer disabled")
        return

    while True:
        await asyncio.sleep(60)  # Keep alive
