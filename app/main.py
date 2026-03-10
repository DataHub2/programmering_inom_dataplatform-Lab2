from fastapi import FastAPI, HTTPException

from services.riksdag_api import fetch_data
from cleaners.clean_ledamoter import clean_ledamoter
from cleaners.clean_kalender import clean_kalender

app = FastAPI(
    title="Riksdagens API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Backend är igång"}

@app.get("/fetch/{source}")
async def fetch(source: str):

    try:
        data = await fetch_data(source)
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clean/ledamoter")
async def ledamoter():

    try:
        raw = await fetch_data("ledamoter")
        cleaned = clean_ledamoter(raw)

        return {
            "count": len(cleaned),
            "data": cleaned
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/clean/kalender")
async def kalender():

    try:
        raw = await fetch_data("kalender")
        cleaned = clean_kalender(raw)

        return {
            "count": len(cleaned),
            "data": cleaned
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))