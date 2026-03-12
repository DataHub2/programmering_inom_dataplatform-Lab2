import httpx
import pandas as pd
from fastapi import HTTPException
import json
from confluent_kafka import Producer

# Configure Kafka producer cluster connection
kafka_conf = {'bootstrap.servers': 'kafka:29092'}
producer = Producer(kafka_conf)

def delivery_report(err, msg):
    # Only report errors to prevent terminal flooding.
    if err is not None:
        print(f"Message delivery failed: {err}")

async def fetch_posts(url: str, csv_path: str):
    # Extract payload from external API asy
    async with httpx.AsyncClient() as client: 
        response = await client.get(url)  

        if response.status_code == 200: 
            cached_data = response.json() 
            
            # extract the actual list of records from the nested JSON
            if "personlista" in cached_data and "person" in cached_data["personlista"]:
                records_to_process = cached_data["personlista"]["person"]
            else:
                # fallback if the API structure differs
                records_to_process = [cached_data] if isinstance(cached_data, dict) else cached_data

            # Standardize structure via Pandas using the flattened list
            cached_df = pd.DataFrame(records_to_process)
            
            print(f"Transmitting {len(cached_df)} individual records to Kafka broker...")
            
            # convert DataFrame into a list of row-level dictionaries
            records = cached_df.to_dict(orient='records')
            
            # stream each extracted row as an individual Kafka event
            for record in records:
                serialized_data = json.dumps(record).encode('utf-8')
                producer.produce('riksdagen_raw_data', value=serialized_data, callback=delivery_report)
            
            # Block until the entire buffer of messages is transmitted
            producer.flush()

            # Maintain local CSV for  backup
            cached_df.to_csv(csv_path, index=False)
            
            print("Kafka streaming and CSV backup complete.")
        else:
            raise HTTPException(status_code=response.status_code, detail="External API error")