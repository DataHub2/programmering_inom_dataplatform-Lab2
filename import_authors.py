import csv
import os
import psycopg
import xmltodict
from dotenv import load_dotenv

load_dotenv()
conn_str = os.getenv("DATABASE_URL")

def importera_forfattare():
    filsokvag = os.path.join("data", "dokument.csv")
    # Denna rad har ändrats så vi ser att vi kör rätt kod:
    print(f"Kopplar författare från XML-data i: {filsokvag}...")

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                with open(filsokvag, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=',', quotechar='"')
                    count = 0

                    for row in reader:
                        doc_id = row.get("dok_id")
                        xml_raw = row.get("dokintressent")

                        # Kolla om det finns XML-data i fältet
                        if not doc_id or not xml_raw or "<intressent>" not in xml_raw:
                            continue

                        try:
                            # Omvandla XML-strängen till en Python-dict
                            data_dict = xmltodict.parse(xml_raw)
                            # Navigera ner till listan av personer
                            intressenter = data_dict.get("dokintressent", {}).get("intressent", [])
                            
                            if isinstance(intressenter, dict):
                                intressenter = [intressenter]

                            for p in intressenter:
                                m_id = p.get("intressent_id")
                                if not m_id: continue

                                sql = """
                                INSERT INTO documents_author (document_id, member_id, party_id, author_order)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT DO NOTHING;
                                """
                                cur.execute(sql, (
                                    doc_id, 
                                    m_id, 
                                    p.get("parti"), 
                                    int(p.get("ordning")) if p.get("ordning") else 1
                                ))
                                count += 1

                        except Exception:
                            continue 
                        
                        if count > 0 and count % 500 == 0:
                            conn.commit()
                            print(f"🔗 {count} kopplingar skapade...")

                conn.commit()
                print(f"Klart! Totalt antal författarkopplingar: {count}")

    except Exception as e:
        print(f"Fel: {e}")

if __name__ == "__main__":
    importera_forfattare()
