from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, requests

app = FastAPI(title="riksdags_data")

EXTERNAL_API = "https://data.riksdagen.se/personlista/?iid=&fnamn=&enamn=&f_ar=&kn=&parti=&valkrets=&org=&utformat=json"

cached_data = [] #tom lista för att lagra det som hämtas från api. Kan bli ett problem ifall större dataset.
# TODO kolla hur annars

async def get_posts():#funktion för att hämta data från det externa api
    async with httpx.AsyncClient() as client: #öppnar en http klient som stängs automatiskt när blocket är klart
        response = await client.get(EXTERNAL_API)  #skickar get förfrågan till riksdagen och väntar på svar
        #await pausar tills svaret kommer tillbaka utan att blockera appen

        if response.status_code == 200: #kollar att anropet gick bra 200=ok
            global cached_data #så funktionen hittar den globala variabeln och inte skapar en ny egen
            cached_data = response.json() #omvandlar svaret till json och sparar detta till det listan
            print("datan är uppdaterad")
        else:
            raise HTTPException(status_code=response.status_code, detail="fel från externt api")

@asynccontextmanager #decorator
async def lifespan():
    yield