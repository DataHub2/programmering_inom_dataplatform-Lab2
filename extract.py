import httpx
import pandas as pd
import json                          # [TILLAGD FRÅN ZAKARIA] behövs för att serialisera rader till JSON innan Kafka
from fastapi import HTTPException
from confluent_kafka import Producer  # [TILLAGD FRÅN ZAKARIA] Kafka-klient för att streama data

from format_files import format_files

# [TILLAGD FRÅN ZAKARIA] Konfigurerar uppkopplingen mot Kafka-brokern
kafka_conf = {'bootstrap.servers': 'kafka:29092'}

# [TILLAGD FRÅN ZAKARIA] Skapar en producer-instans som används för att skicka meddelanden
producer = Producer(kafka_conf)


# [TILLAGD FRÅN ZAKARIA] Callback-funktion som körs efter varje skickat meddelande
# Skriver bara ut fel så att terminalen inte översvämmas av lyckade leveranser
def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")


# [FRÅN MAIN] Huvudfunktion för att hämta, transformera och spara data
# [ÄNDRAD] kafka_topic är ny parameter — om None skippas Kafka-steget helt
async def fetch_posts(
    url: str,           # [FRÅN MAIN] URL till externt API
    csv_path: str,      # [FRÅN MAIN] Sökväg där CSV-filen sparas lokalt
    record_path: list = None,  # [FRÅN MAIN] Navigerar nästlad JSON, t.ex. ["kalender", "händelse"]
    keep: list = None,         # [FRÅN MAIN] Vilka kolumner som ska behållas efter formatering
    rename: dict = None,       # [FRÅN MAIN] Namnbyte av kolumner, t.ex. {"id": "person_id"}
    kafka_topic: str = None,   # [TILLAGD FRÅN ZAKARIA] Topic att streama till, t.ex. "riksdagen_raw_data"
):
    # [FRÅN MAIN] Öppnar en asynkron HTTP-klient som stängs automatiskt när blocket är klart
    async with httpx.AsyncClient() as client:

        # [FRÅN MAIN] Skickar GET-förfrågan och väntar på svar, avbryter efter 30 sekunder
        response = await client.get(url, timeout=30)

        if response.status_code == 200:  # [FRÅN MAIN] 200 = lyckat anrop

            # [FRÅN MAIN] Omvandlar svaret till en Python-dict
            cached_data = response.json()

            try:
                if record_path:  # [FRÅN MAIN] Om record_path är angiven, navigera ner i den nästlade JSON-strukturen
                    nested = cached_data
                    for key in record_path:  # [FRÅN MAIN] Går ner ett lager i taget, t.ex. cached_data["kalender"]["händelse"]
                        nested = nested[key]
                    cached_df = pd.json_normalize(nested)   # [FRÅN MAIN] Plattar ut varje post till en rad i DataFrame
                else:
                    cached_df = pd.json_normalize(cached_data)  # [FRÅN MAIN] Fallback om JSON redan är platt

                # [FRÅN MAIN] Kör formatering direkt efter hämtning så CSV alltid är städad
                cached_df = format_files(cached_df, keep=keep, rename=rename)

                # [TILLAGD FRÅN ZAKARIA] Kafka-streaming — körs bara om kafka_topic är angiven
                if kafka_topic:
                    # [FRÅN ZAKARIA] Omvandlar DataFrame till en lista av dictionaries, en per rad
                    records = cached_df.to_dict(orient='records')

                    print(f"Transmitting {len(records)} records to Kafka topic '{kafka_topic}'...")

                    for record in records:  # [FRÅN ZAKARIA] Loopar igenom varje rad och skickar den som ett eget Kafka-event
                        serialized_data = json.dumps(record).encode('utf-8')  # [FRÅN ZAKARIA] Serialiserar raden till bytes
                        producer.produce(kafka_topic, value=serialized_data, callback=delivery_report)  # [FRÅN ZAKARIA] Skickar till Kafka

                    producer.flush()  # [FRÅN ZAKARIA] Blockerar tills alla meddelanden i bufferten är skickade

                    print("Kafka streaming complete.")

                # [FRÅN MAIN] Sparar den formaterade DataFrame till CSV utan radnummer-kolumn
                cached_df.to_csv(csv_path, index=False)

                print("Datan är uppdaterad.")  # [FRÅN MAIN]

            except (KeyError, TypeError) as e:
                # [FRÅN MAIN] KeyError = record_path stämmer inte med JSON-strukturen
                # [FRÅN MAIN] TypeError = JSON-strukturen är inte ett dict som förväntat
                raise HTTPException(
                    status_code=500,
                    detail="Kunde inte tolka JSON"
                )

        else:
            # [FRÅN MAIN] Vidarebefordrar felkoden från det externa API:et
            raise HTTPException(status_code=response.status_code, detail="Fel från externt API")
