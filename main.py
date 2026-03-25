from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from exract.extract import fetch_posts
from exract.config import APIS


@asynccontextmanager
async def lifespan(app: FastAPI): # styr vad som händer när appen startar och stängs ner
    scheduler = AsyncIOScheduler() # skapar en scheduler som håller koll på när jobb ska köras

    for api in APIS: # loopa igenom alla API:er i listan
        scheduler.add_job(fetch_posts, trigger="interval", hours=24, args=[api["url"], api["csv"], api["record_path"]]) # schemalägg hämtning var 24:e timme
        await fetch_posts(api["url"], api["csv"], api["record_path"], api["kafka_topic"]) # hämta direkt vid uppstart så data inte är tom

    scheduler.start() # starta schedulern
    yield # appen lever här och tar emot requests
    scheduler.shutdown() # stäng ner schedulern när appen stängs ner

app = FastAPI(title="riksdags_data", lifespan=lifespan) # skapa appen och koppla lifespanshutdown()
