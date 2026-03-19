import psycopg
import os
from dotenv import load_dotenv

load_dotenv()
conn_str = os.getenv("DATABASE_URL")

def logga_import_status(kalla, status, antal):
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                sql = """
                INSERT INTO pipeline_logs (source, status, records_inserted, finished_at)
                VALUES (%s, %s, %s, NOW());
                """
                cur.execute(sql, (kalla, status, antal))
                print(f"Loggade importen för {kalla} i pipeline_logs!")
    except Exception as e:
        print(f"Kunde inte logga: {e}")

if __name__ == "__main__":
    # Exempel: Logga att du precis blev klar med anföranden
    logga_import_status("anforanden.csv", "SUCCESS", 5000) # Byt ut 5000 mot ditt riktiga antal sen