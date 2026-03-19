import csv
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
conn_str = os.getenv("DATABASE_URL")

def importera_ledamoter_final():
    filsokvag = os.path.join("data", "ledamoter.csv")
    print(f"🚀 Synkar ledamöter från: {filsokvag}...")

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                with open(filsokvag, mode='r', encoding='utf-8-sig') as f:
                    # Vi använder kommatecken som separator
                    reader = csv.DictReader(f, delimiter=',')
                    count = 0

                    for row in reader:
                        m_id = row.get("intressent_id")
                        if not m_id: continue

                        # Vi mappar mot de exakta namnen från ditt head-test:
                        # fodd_ar, kon, efternamn, tilltalsnamn, parti, valkrets, status
                        sql = """
                        INSERT INTO members (member_id, first_name, last_name, party_id, district, status, gender, birth_year)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (member_id) DO UPDATE SET
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            birth_year = EXCLUDED.birth_year,
                            district = EXCLUDED.district,
                            status = EXCLUDED.status,
                            gender = EXCLUDED.gender;
                        """
                        
                        fodd = row.get("fodd_ar")
                        birth_year = int(fodd) if fodd and str(fodd).isdigit() else None

                        cur.execute(sql, (
                            m_id, 
                            row.get("tilltalsnamn"), 
                            row.get("efternamn"), 
                            row.get("parti"), 
                            row.get("valkrets"), 
                            row.get("status"), 
                            row.get("kon"), 
                            birth_year
                        ))
                        
                        count += 1
                        if count % 100 == 0:
                            conn.commit()
                            print(f"✅ Uppdaterat {count} ledamöter... (Senaste: {row.get('tilltalsnamn')} {row.get('efternamn')})")

                conn.commit()
                print(f"🏆 KLART! Nu är alla 488+ ledamöter uppdaterade med födelseår och namn.")

    except Exception as e:
        print(f"❌ Fel vid import: {e}")

if __name__ == "__main__":
    importera_ledamoter_final()