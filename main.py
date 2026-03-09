from contextlib import asynccontextmanager
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, requests
from starlette import status

EXTERNAL_API = "https://data.riksdagen.se/personlista/?iid=&fnamn=&enamn=&f_ar=&kn=&parti=&valkrets=&org=&utformat=json"

cached_data = [] #tom lista för att lagra det som hämtas från api. Kan bli ett problem ifall större dataset.
# TODO kolla hur annars

async def fetch_posts():#funktion för att hämta data från det externa api
    async with httpx.AsyncClient() as client: #öppnar en http klient som stängs automatiskt när blocket är klart
        response = await client.get(EXTERNAL_API)  #skickar get förfrågan till riksdagen och väntar på svar
        #await pausar tills svaret kommer tillbaka utan att blockera appen

        if response.status_code == 200: #kollar att anropet gick bra 200=ok
            global cached_data #så funktionen hittar den globala variabeln och inte skapar en ny egen
            cached_data = response.json() #omvandlar svaret till json och sparar detta till det listan
            # TODO här kanske det är rimligt att lägga in kafka? att kafka reagerar när man uppdaterar
            print("datan är uppdaterad")
        else:
            raise HTTPException(status_code=response.status_code, detail="fel från externt api")

@asynccontextmanager #decorator för att göra funktionen till en context manager
#gör att fastapi förstår att denna funktionen ska användas som ett lifespan
async def lifespan(app: FastAPI):#styr vad som händer när appen startar och stängs ner

    scheduler = AsyncIOScheduler() #skapa en ny scheduler som håller koll på när saker ska köras

    scheduler.add_job(fetch_posts, trigger="interval", hours=24)  #ge schedulern ett jobb att köra get_posts en gång per dygn

    # TODO kolla hur vi ska hantera att den bara uppdaterar när appen är startad lokalt. Kanske ok för detta projekt?
    scheduler.start() #startar schedulern och börjar hålla koll på tiden

    await fetch_posts() #hämtar data direkt vid uppstarten så att cached_data inte är tom

    yield #det som är ovanför yield körs vid uppstart och det som är nedanför körs vid nedstängning

    scheduler.shutdown()

app = FastAPI(title="riksdags_data", lifespan=lifespan) #skapar vår app kopplar detta till lifespan

@app.get("/posts") 
async def get_posts():
    if not cached_data: #kolla om cached data är tom
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data ej laddad")
    return cached_data

