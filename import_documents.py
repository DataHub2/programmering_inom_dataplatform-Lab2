# import_authors.py, men du kan låta den vara så länge. Eftersom den gav 0 rader betyder det bara att den specifika CSV-filen saknade den datan just nu.
import csv
import os
import psycopg
from dotenv import load_dotenv

# Laddar in .env
load_dotenv()
conn_str = os.getenv("DATABASE_URL")

def importera_dokument():
    filsokvag = os.path.join("data", "dokument.csv")
    
    if not os.path.exists(filsokvag):
        print(f"Hittade inte filen på: {filsokvag}")
        return

    print(f"Startar import (med kommatecken) från: {filsokvag}...")

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                with open(filsokvag, mode='r', encoding='utf-8-sig') as f:
                    # ÄNDRAT: Vi använder delimiter=',' här
                    reader = csv.DictReader(f, delimiter=',', quotechar='"')
                    count = 0

                    for row in reader:
                        doc_id = row.get("dok_id")
                        if not doc_id: 
                            continue

                        # SQL för tabellen 'documents'
                        sql = """
                        INSERT INTO documents (document_id, title, document_type, date, riksmote, organ, status, html_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            status = EXCLUDED.status;
                        """
                        
                        cur.execute(sql, (
                            doc_id,
                            row.get("titel"),
                            row.get("doktyp"),
                            row.get("datum"),
                            row.get("rm"),
                            row.get("organ"),
                            row.get("status"),
                            row.get("url")
                        ))
                        
                        count += 1
                        if count % 500 == 0:
                            conn.commit()
                            print(f"💾 {count} dokument sparade...")

                conn.commit()
                print(f"Klart! Totalt sparade dokument: {count}")

    except Exception as e:
        print(f"Fel vid import: {e}")

if __name__ == "__main__":
    importera_dokument()
