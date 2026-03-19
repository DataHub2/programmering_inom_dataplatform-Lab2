import csv
import os
import psycopg
from dotenv import load_dotenv

# 1. Ladda in anslutningen
load_dotenv()
conn_str = os.getenv("DATABASE_URL")

def fixa_ledamot_detaljer():
    # Vi pekar på filen i din data-folder
    filsokvag = os.path.join("data", "ledamoter.csv") 
    
    if not os.path.exists(filsokvag):
        print(f"Hittade inte filen: {filsokvag}")
        return

    print(f"Uppdaterar ledamöter i Supabase från: {filsokvag}...")

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                with open(filsokvag, mode='r', encoding='utf-8-sig') as f:
                    # Vi använder kommatecken (,) som vi såg i ditt 'head'-test
                    reader = csv.DictReader(f, delimiter=',', quotechar='"')
                    count = 0

                    for row in reader:
                        m_id = row.get("Id") or row.get("intressent_id")
                        if not m_id: continue

                        # UPDATE-logik för att fylla i namnen på de "skal" vi skapade förut
                        sql = """
                        UPDATE members 
                        SET 
                            first_name = %s,
                            last_name = %s,
                            district = %s,
                            status = %s,
                            gender = %s,
                            birth_year = %s
                        WHERE member_id = %s;
                        """
                        
                        birth_year = int(row.get("Född")) if str(row.get("Född")).isdigit() else None
                        
                        cur.execute(sql, (
                            row.get("Förnamn"),
                            row.get("Efternamn"),
                            row.get("Valkrets"),
                            row.get("Status"),
                            row.get("Kön"),
                            birth_year,
                            m_id
                        ))
                        
                        count += 1
                        if count % 100 == 0:
                            conn.commit()
                            print(f"Uppdaterat {count} ledamöter...")

                conn.commit()
                print(f"Klart! Nu har alla ledamöter namn och detaljer.")

    except Exception as e:
        print(f"Fel: {e}")

if __name__ == "__main__":
    fixa_ledamot_detaljer()