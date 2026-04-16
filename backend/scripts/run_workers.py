"""
Run RocketMQ consumer workers.
Usage: python scripts/run_workers.py
"""
import asyncio
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("workers")


async def main():
    logger.info("Starting consumer workers...")

    from app.mq.chat_consumer import run_chat_consumer
    from app.mq.artifact_consumer import run_artifact_consumer

    tasks = [
        asyncio.create_task(run_chat_consumer()),
        asyncio.create_task(run_artifact_consumer()),
    ]

    shutdown_event = asyncio.Event()

    def handle_signal():
        logger.info("Received shutdown signal, stopping workers...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    logger.info("Workers running. Press Ctrl+C to stop.")
    await shutdown_event.wait()

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Workers stopped.")


if __name__ == "__main__":
    asyncio.run(main())
