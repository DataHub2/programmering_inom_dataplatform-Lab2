import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="riksdags_data")

EXTERNAL_API = "https://data.riksdagen.se/personlista/?iid=&fnamn=&enamn=&f_ar=&kn=&parti=&valkrets=&org=&utformat=json"

@app.get("/posts")
async def get_posts():
    async with httpx.AsyncClient() as client:
        response = await client.get(EXTERNAL_API)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="fel från externt api")

    return response.json()