from contextlib import asynccontextmanager

import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from extract import fetch_posts
from transform import transform_data

#Här fyller man i vilka api man vill hämta man anger url och vad csv filen ska heta. Kan göras hur många som helst
#för att köra koden kör "uvicorn main:app --reload"
APIS = [
    {"url":"https://data.riksdagen.se/personlista/?iid=&fnamn=&enamn=&f_ar=&kn=&parti=&valkrets=&rdlstatus=tjanst&org=&utformat=json&sort=sorteringsnamn&sortorder=asc&termlista="
        , "csv":"riksdagen.csv" },
]


@asynccontextmanager
async def lifespan(app: FastAPI): # styr vad som händer när appen startar och stängs ner
    scheduler = AsyncIOScheduler() # skapar en scheduler som håller koll på när jobb ska köras

    for api in APIS: # loopa igenom alla API:er i listan
        scheduler.add_job(fetch_posts, trigger="interval", hours=24, args=[api["url"], api["csv"]]) # schemalägg hämtning var 24:e timme
        await fetch_posts(api["url"], api["csv"]) # hämta direkt vid uppstart så data inte är tom

    scheduler.start() # starta schedulern
    yield # appen lever här och tar emot requests
    scheduler.shutdown() # stäng ner schedulern när appen stängs ner

app = FastAPI(title="riksdags_data", lifespan=lifespan) # skapa appen och koppla lifespanshutdown()

#TODO ska detta ligga här?
def csv_to_df(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path)

raw_df_riksdagen = csv_to_df("riksdagen.csv")

transformed_df_riksdagen = transform_data(raw_df_riksdagen)#exempel på hur man använder transform

# TODO att ha en posts endpoint kan vara onödigt i det hela dataflödet. Men kan vara bra att ha lvar nu under utveckling för att enklare felsöka

# @app.get("/posts")
# async def get_posts():
#     if not cached_data: #kolla om cached data är tom
#         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data ej laddad")
#     return cached_data
