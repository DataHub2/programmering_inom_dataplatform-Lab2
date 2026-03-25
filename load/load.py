import pandas as pd
import os
import sys
sys.path.insert(0, "../transform")

from clean import clean
from reject import transform
from confluent_kafka import Consumer
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

# connect to supabase using env variables
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# maps kafka topics to supabase table names
TABLE_MAP = {
    "riksdagen_raw_data": "speeches_raw",
}

def load_to_supabase(df: pd.DataFrame, table_name: str):
    """loads transformed dataframe into supabase - handles nan values properly"""
    df = df.where(pd.notna(df), None)
    df = df.astype(object).where(pd.notna(df), None)
    records = []
    for record in df.to_dict(orient="records"):
        clean_record = {k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in record.items()}
        records.append(clean_record)

    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        supabase.table(table_name).upsert(batch).execute()
    print(f" {len(records)} rader laddade till {table_name}")

def consume(): # -> här laddar kafka in i auto mode
    """listens to kafka and writes new data to supabase automatically""" 
    consumer = Consumer({
        "bootstrap.servers": "kafka:29092",
        "group.id": "supabase-loader",
        "auto.offset.reset": "earliest"
    })
    consumer.subscribe(list(TABLE_MAP.keys()))
    print("listening on Kafka...")
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        record = json.loads(msg.value().decode("utf-8"))
        table = TABLE_MAP[msg.topic()]
        supabase.table(table).upsert(record).execute()
        print(f"wrote row to {table}")

if __name__ == "__main__":
    # read raw data
    df_ledamoter  = clean(pd.read_csv("../data/ledamoter.csv"))
    df_voteringar = clean(pd.read_csv("../data/voteringar.csv"))
    df_anforanden = clean(pd.read_csv("../data/anforanden.csv"))
    df_kalender   = clean(pd.read_csv("../data/kalender.csv"))
    df_dokument   = clean(pd.read_csv("../data/dokument.csv"))

    print(" Clean klar")

    # run full transform (flag + reject).
    result = transform(df_ledamoter, df_voteringar, df_anforanden, df_kalender, df_dokument)

    print(" Transform klar")

    # load to supabase
    load_to_supabase(result["ledamoter"],  "members_raw")
    load_to_supabase(result["voteringar"], "votes_raw")
    load_to_supabase(result["anforanden"], "speeches_raw")
    load_to_supabase(result["kalender"],   "calendar_raw")
    load_to_supabase(result["dokument"],   "documents_raw")