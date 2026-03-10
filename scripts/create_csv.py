import asyncio
import pandas as pd
from pathlib import Path
import sys

# gör så Python hittar project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.riksdag_api import fetch_data

from cleaners.clean_ledamoter import clean_ledamoter
from cleaners.clean_kalender import clean_kalender
from cleaners.clean_voteringar import clean_voteringar
from cleaners.clean_dokument import clean_dokument
from cleaners.clean_anforanden import clean_anforanden


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


async def create_csv(source: str, cleaner, filename: str):

    print(f"Hämtar data från: {source}")

    try:
        raw = await fetch_data(source)

        if not raw:
            print(f"Ingen data hämtades för {source}")
            return

        cleaned = cleaner(raw)

        if not cleaned:
            print(f"Ingen data efter cleaning för {source}")
            return

        df = pd.DataFrame(cleaned)

        path = DATA_DIR / filename
        df.to_csv(path, index=False)

        print(f"{filename} skapad ({len(df)} rader)")

    except Exception as e:
        print(f"Fel vid skapande av {filename}: {e}")


async def main():

    sources = [
        ("ledamoter", clean_ledamoter, "ledamoter.csv"),
        ("kalender", clean_kalender, "kalender.csv"),
        ("voteringar", clean_voteringar, "voteringar.csv"),
        ("dokument", clean_dokument, "dokument.csv"),
        ("anforanden", clean_anforanden, "anforanden.csv"),
    ]

    tasks = [create_csv(*s) for s in sources]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())