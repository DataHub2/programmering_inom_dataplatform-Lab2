import os
import psycopg
from dotenv import load_dotenv

# Laddar in din .env-fil
load_dotenv()
conn_str = os.getenv("DATABASE_URL")

print(f"Försöker ansluta till: {conn_str[:40]}...") # Visar bara början av URL:en för säkerhet

try:
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            # Vi kollar om vi kan läsa från din members-tabell
            cur.execute("SELECT COUNT(*) FROM members;")
            result = cur.fetchone()
            print(f"✅ Anslutning lyckades via psycopg!")
            print(f"📊 Det finns {result[0]} ledamöter i din databas just nu.")
except Exception as e:
    print(f"❌ Kunde inte ansluta: {e}")
