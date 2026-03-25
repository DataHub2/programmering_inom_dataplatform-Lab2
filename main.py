import threading
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from extract.extract import fetch_posts
from extract.config import APIS
from load.load import consume

logger = logging.getLogger(__name__)


def consume_with_error_handling(stop_event):
    # retry loop — restarts consumer if it crashes unexpectedly
    while not stop_event.is_set():
        try:
            consume(stop_event)
        except Exception as e:
            logger.error(f"Kafka consumer crashed, restarting in 10s: {e}")
            stop_event.wait(10)  # wait before retrying to avoid rapid crash loops


@asynccontextmanager
async def lifespan(app: FastAPI):
    # start Kafka consumer in a background thread so it runs alongside FastAPI
    stop_event = threading.Event()
    thread = threading.Thread(target=consume_with_error_handling, args=[stop_event], daemon=True)
    thread.start()

    scheduler = AsyncIOScheduler()

    for api in APIS:
        # fetch data immediately on startup so the database is never empty
        try:
            await fetch_posts(api["url"], api["csv"], api["record_path"], api["kafka_topic"])
        except Exception as e:
            logger.error(f"Startup fetch failed for {api['url']}: {e}")  # log and continue to next API

        # schedule recurring fetch every 24 hours
        scheduler.add_job(
            fetch_posts,
            trigger="interval",
            hours=24,
            args=[api["url"], api["csv"], api["record_path"], api["kafka_topic"]],
            misfire_grace_time=300,   # allow up to 5 min delay before skipping a missed job
            coalesce=True,            # if multiple runs were missed, only run once on recovery
        )

    scheduler.start()
    yield  # app is live and accepting requests here
    stop_event.set()   # signal consumer thread to stop
    scheduler.shutdown()


app = FastAPI(title="riksdags_data", lifespan=lifespan)