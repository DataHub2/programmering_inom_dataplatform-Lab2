import pandas as pd
import os
import sys
from datetime import datetime, timezone
sys.path.insert(0, "transform")

from clean import clean
from reject import transform
from confluent_kafka import Consumer
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

TABLE_MAP = {
    "riksdagen_raw_data": "speeches_raw",
}


def load_to_supabase(df: pd.DataFrame, table_name: str):
    """Loads transformed dataframe into supabase — handles nan values properly."""
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


def log_pipeline(
    source: str,
    records_inserted: int,
    status: str = "success",
    error_message: str = None,
    started_at: datetime = None,
):
    """Writes a pipeline run entry to pipeline_logs in Supabase."""
    finished_at = datetime.now(timezone.utc)
    started = started_at or finished_at
    duration_ms = int((finished_at - started).total_seconds() * 1000)

    supabase.table("pipeline_logs").insert({
        "source":           source,
        "records_inserted": records_inserted,
        "records_failed":   0,
        "status":           status,
        "error_message":    error_message,
        "started_at":       started.isoformat(),
        "finished_at":      finished_at.isoformat(),
        "duration_ms":      duration_ms,
        "triggered_by":     "load.py",
    }).execute()
    print(f" Pipeline-logg sparad för {source} — {records_inserted} rader, status: {status}")


def consume(stop_event=None):
    """Listens to Kafka and writes new data to Supabase automatically."""
    consumer = Consumer({
        "bootstrap.servers": "kafka:29092",
        "group.id": "supabase-loader",
        "auto.offset.reset": "earliest"
    })
    consumer.subscribe(list(TABLE_MAP.keys()))
    print("Listening on Kafka...")
    while True:
        if stop_event and stop_event.is_set():
            break
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        record = json.loads(msg.value().decode("utf-8"))
        table = TABLE_MAP[msg.topic()]
        supabase.table(table).upsert(record).execute()
        print(f"Wrote row to {table}")
    consumer.close()


if __name__ == "__main__":
    df_ledamoter  = clean(pd.read_csv("data/ledamoter.csv"))
    df_voteringar = clean(pd.read_csv("data/voteringar.csv"))
    df_anforanden = clean(pd.read_csv("data/anforanden.csv"))
    df_kalender   = clean(pd.read_csv("data/kalender.csv"))
    df_dokument   = clean(pd.read_csv("data/dokument.csv"))

    print(" Clean klar")

    result = transform(df_ledamoter, df_voteringar, df_anforanden, df_kalender, df_dokument)

    print(" Transform klar")

    sources = [
        (result["ledamoter"],  "members_raw",   "ledamoter"),
        (result["voteringar"], "votes_raw",      "voteringar"),
        (result["anforanden"], "speeches_raw",   "anforanden"),
        (result["kalender"],   "calendar_raw",   "kalender"),
        (result["dokument"],   "documents_raw",  "dokument"),
    ]

    for df, table, source in sources:
        started = datetime.now(timezone.utc)
        try:
            load_to_supabase(df, table)
            log_pipeline(
                source=source,
                records_inserted=len(df),
                status="success",
                started_at=started,
            )
        except Exception as e:
            log_pipeline(
                source=source,
                records_inserted=0,
                status="error",
                error_message=str(e),
                started_at=started,
            )
            print(f" Fel vid laddning av {source}: {e}")