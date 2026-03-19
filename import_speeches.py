import csv
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
conn_str = os.getenv("DATABASE_URL")

def importera_anforanden():
    filsokvag = os.path.join("data", "anforanden.csv")
    print(f"Startar import (med automatisk text-trimning)...")

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                with open(filsokvag, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=',', quotechar='"')
                    count = 0

                    for row in reader:
                        s_id = row.get("anforande_id")
                        m_id = row.get("intressent_id")
                        
                        # Vi klipper av party_id och riksmote till max 10 tecken för att slippa felet
                        p_id = (row.get("parti") or "UP")[:10]
                        rm = (row.get("dok_rm") or "")[:10]
                        
                        d_id = row.get("rel_dok_id", "").strip()
                        if d_id == "" or d_id == "()": d_id = None 

                        if not s_id or not m_id:
                            continue

                        # 1. FIX: Skapa PARTIET
                        cur.execute("INSERT INTO parties (party_id, party_name) VALUES (%s, %s) ON CONFLICT (party_id) DO NOTHING;", (p_id, p_id))

                        # 2. FIX: Skapa LEDAMOTEN
                        cur.execute("INSERT INTO members (member_id, party_id) VALUES (%s, %s) ON CONFLICT (member_id) DO NOTHING;", (m_id, p_id))

                        # 3. FIX: Skapa DOKUMENTET om det finns
                        if d_id:
                            cur.execute("INSERT INTO documents (document_id) VALUES (%s) ON CONFLICT (document_id) DO NOTHING;", (d_id,))

                        # 4. Spara anförandet
                        sql = """
                        INSERT INTO speeches (speech_id, member_id, party_id, riksmote, date, debate_title, speech_type, body_text, document_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (speech_id) DO NOTHING;
                        """
                        cur.execute(sql, (
                            s_id, m_id, p_id, 
                            rm, # Denna är nu max 10 tecken
                            row.get("dok_datum"), 
                            row.get("avsnittsrubrik"), 
                            row.get("kammaraktivitet"), 
                            row.get("anforandetext"), 
                            d_id
                        ))
                        
                        count += 1
                        if count % 500 == 0:
                            conn.commit()
                            print(f"{count} anföranden bearbetade...")

                conn.commit()
                print(f"Klart! Totalt antal anföranden: {count}")

    except Exception as e:
        print(f"Fel vid import: {e}")

if __name__ == "__main__":
    importera_anforanden()