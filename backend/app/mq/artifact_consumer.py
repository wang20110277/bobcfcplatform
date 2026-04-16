"""RocketMQ consumer for artifact generation tasks."""
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

ARTIFACT_TOPIC = "artifact-topic"


async def run_artifact_consumer():
    """
    Consumes artifact generation messages from RocketMQ.
    Generates content via Gemini, uploads to MinIO, updates DB.

    For now, this is a placeholder. The synchronous /api/artifacts/generate
    endpoint handles requests directly.
    """
    logger.info("Artifact consumer starting (placeholder - requires RocketMQ broker)")
    try:
        from rocketmq.client import PushConsumer
    except ImportError:
        logger.warning("rocketmq-client-python not installed, artifact consumer disabled")
        return

    while True:
        await asyncio.sleep(60)
