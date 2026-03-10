import httpx
import pandas as pd
from fastapi import HTTPException


async def fetch_posts(url: str, csv_path: str):#funktion för att hämta data från det externa api
    async with httpx.AsyncClient() as client: #öppnar en http klient som stängs automatiskt när blocket är klart
        response = await client.get(url)  #skickar get förfrågan till riksdagen och väntar på svar
        #await pausar tills svaret kommer tillbaka utan att blockera appen

        if response.status_code == 200: #kollar att anropet gick bra 200=ok
            cached_data = response.json() #omvandlar svaret till json och sparar detta till det listan
            cached_df = pd.DataFrame.from_dict(cached_data)
            cached_df.to_csv(csv_path, index=False)
            # TODO här kanske det är rimligt att lägga in kafka? att kafka reagerar när man uppdaterar
            print("datan är uppdaterad")
        else:
            raise HTTPException(status_code=response.status_code, detail="fel från externt api")