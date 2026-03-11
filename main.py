from contextlib import asynccontextmanager

import httpx
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from extract import fetch_posts
from transform import transform_data
from config import APIS


@asynccontextmanager
async def lifespan(app: FastAPI): # styr vad som händer när appen startar och stängs ner
    scheduler = AsyncIOScheduler() # skapar en scheduler som håller koll på när jobb ska köras

    for api in APIS: # loopa igenom alla API:er i listan
        scheduler.add_job(fetch_posts, trigger="interval", hours=24, args=[api["url"], api["csv"], api["record_path"], api.get("keep"), api.get("rename")]) # schemalägg hämtning var 24:e timme
        await fetch_posts(api["url"], api["csv"], api["record_path"], api.get("keep"), api.get("rename")) # hämta direkt vid uppstart så data inte är tom

    scheduler.start() # starta schedulern
    yield # appen lever här och tar emot requests
    scheduler.shutdown() # stäng ner schedulern när appen stängs ner

app = FastAPI(title="riksdags_data", lifespan=lifespan) # skapa appen och koppla lifespanshutdown()


# #TODO ska detta ligga här?
# def csv_to_df(csv_path: str) -> pd.DataFrame:
#     return pd.read_csv(csv_path)
#
# raw_df_riksdagen = csv_to_df("data/riksdagen.csv")
#
# transformed_df_riksdagen = transform_data(raw_df_riksdagen)#exempel på hur man använder transform
#
# print(transformed_df_riksdagen.head())

# TODO att ha en posts endpoint kan vara onödigt i det hela dataflödet. Men kan vara bra att ha lvar nu under utveckling för att enklare felsöka

# @app.get("/posts")
# async def get_posts():
#     if not cached_data: #kolla om cached data är tom
#         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data ej laddad")
#     return cached_data
#debug code
# @app.get("/debug/{endpoint}")
# async def debug_endpoint(endpoint: str):
#     urls = {
#         "kalender": "https://data.riksdagen.se/kalender/?org=kamm&utformat=json",
#         "ledamoter": "https://data.riksdagen.se/personlista/?utformat=json",
#         "dokument": "https://data.riksdagen.se/dokumentlista/?sz=500&utformat=json",
#         "voteringar": "https://data.riksdagen.se/voteringlista/?sz=500&utformat=json",
#         "anforanden": "https://data.riksdagen.se/anforandelista/?sz=500&utformat=json",
#     }
#     async with httpx.AsyncClient() as client:
#         r = await client.get(urls[endpoint], timeout=30)
#         data = r.json()
#
#         result = {}
#         for k1, v1 in data.items():
#             if isinstance(v1, dict):
#                 result[k1] = {}
#                 for k2, v2 in v1.items():
#                     if isinstance(v2, list):
#                         # detta är datan vi vill åt — visa första posten
#                         result[k1][k2] = f"LIST med {len(v2)} poster → första: {v2[0] if v2 else 'tom'}"
#                     else:
#                         result[k1][k2] = v2  # metadata som @antal
#             elif isinstance(v1, list):
#                 result[k1] = f"LIST med {len(v1)} poster → första: {v1[0] if v1 else 'tom'}"
#             else:
#                 result[k1] = v1
#
#         return result