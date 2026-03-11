import httpx
import pandas as pd
from fastapi import HTTPException

from format_files import format_files


async def fetch_posts(
    url: str,
    csv_path: str,
    record_path: list = None,
    keep: list = None,
    rename: dict = None):#funktion för att hämta data från det externa api

    async with httpx.AsyncClient() as client: #öppnar en http klient som stängs automatiskt när blocket är klart
        response = await client.get(url, timeout=30)  #skickar get förfrågan till riksdagen och väntar på svar, timeout efter 30 s
        #await pausar tills svaret kommer tillbaka utan att blockera appen

        if response.status_code == 200: #kollar att anropet gick bra 200=ok
            cached_data = response.json() #omvandlar svaret till json och sparar detta till det listan
            # print(f"JSON-nycklar från {url}: {list(cached_data.keys())}") #debug code
            # nested = cached_data[list(cached_data.keys())[0]]  # gå ner ett lager automatiskt
            # print(f"  → nästa nivå: {list(nested.keys()) if isinstance(nested, dict) else type(nested)}")
            try:
                if record_path: # Riksdagens API returnerar nästlad JSON, record_path = ["kalender", "händelse"] navigerar oss till listan med poster
                    nested = cached_data
                    for key in record_path: nested = nested[key] #går ner ett lager i taget
                    cached_df = pd.json_normalize(nested)  # plattar ut varje post till en rad i dataframen
                else:
                    cached_df = pd.json_normalize(cached_data)  # fallback om JSON:en redan är platt


                cached_df = format_files(cached_df, keep=keep, rename=rename)# kör transform direkt efter hämtning så CSV alltid är städad
                cached_df.to_csv(csv_path, index=False)  # sparar till CSV utan radnummer-kolumn
                # TODO här kanske det är rimligt att lägga in kafka? att kafka reagerar när man uppdaterar
                print("datan är uppdaterad")
            except (KeyError, TypeError) as e:
                # KeyError = record_path stämmer inte med JSON-strukturen
                # TypeError = JSON-strukturen är inte ett dict som förväntat
                raise HTTPException(
                    status_code=500,
                    detail= "Kunde inte tolka JSON"
                )

        else:
            raise HTTPException(status_code=response.status_code, detail="fel från externt api")

