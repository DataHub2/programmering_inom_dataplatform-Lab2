import csv
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
conn_str = os.getenv("DATABASE_URL")

def importera_voteringar():
    filsokvag = os.path.join("data", "voteringar.csv")
    print(f"Startar import (nu med partier, ledamöter och dokument)...")

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                with open(filsokvag, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=',')
                    count = 0

                    for row in reader:
                        v_id = row.get("votering_id")
                        d_id = row.get("dok_id")
                        m_id = row.get("intressent_id")
                        p_id = row.get("parti", "UP")
                        
                        if not v_id or not m_id:
                            continue

                        # 1. FIX: Skapa PARTIET om det saknas (NYTT!)
                        if p_id:
                            cur.execute("INSERT INTO parties (party_id, party_name) VALUES (%s, %s) ON CONFLICT (party_id) DO NOTHING;", (p_id, p_id))

                        # 2. FIX: Skapa DOKUMENTET om det saknas
                        if d_id:
                            cur.execute("INSERT INTO documents (document_id) VALUES (%s) ON CONFLICT (document_id) DO NOTHING;", (d_id,))

                        # 3. FIX: Skapa LEDAMOTEN om hen saknas
                        cur.execute("""
                            INSERT INTO members (member_id, first_name, last_name, party_id) 
                            VALUES (%s, %s, %s, %s) 
                            ON CONFLICT (member_id) DO NOTHING;
                        """, (m_id, row.get("fornamn"), row.get("efternamn"), p_id))

                        # 4. Spara i 'votes'
                        cur.execute("""
                            INSERT INTO votes (vote_id, document_id, topic, riksmote, date)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (vote_id) DO NOTHING;
                        """, (v_id, d_id, row.get("beteckning"), row.get("rm"), row.get("systemdatum")))

                        # 5. Spara i 'vote_results'
                        cur.execute("""
                            INSERT INTO vote_results (vote_id, member_id, party_id, vote)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING;
                        """, (v_id, m_id, p_id, row.get("rost")))

                        count += 1
                        if count % 2000 == 0:
                            conn.commit()
                            print(f"{count} rader bearbetade...")

                conn.commit()
                print(f"Klart! Totalt sparade: {count}")

    except Exception as e:
        print(f"Fel vid import: {e}")

if __name__ == "__main__":
    importera_voteringar()

