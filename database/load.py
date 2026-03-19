import os
import psycopg
import pandas as pd
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Ladda miljövariabler (för Supabase-anslutningen)
load_dotenv()

# Hämta connection string från .env
DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Skapar en anslutning till Postgres med psycopg 3."""
    return psycopg.connect(DB_URL, row_factory=dict_row)

def load_to_db(result_dict: dict):
    """
    Huvudfunktion för att ladda data i rätt ordning enligt kollegans instruktioner.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            
            # 1. MEMBERS (ledamoter)
            if "ledamoter" in result_dict:
                df = result_dict["ledamoter"]
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO members (member_id, first_name, last_name, party_id, district, status, gender, birth_year, image_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (member_id) DO NOTHING
                    """, (row['intressent_id'], row['tilltalsnamn'], row['efternamn'], row['parti'], 
                          row['valkrets'], row['status'], row['kon'], row['fodd_ar'], row['bild_url_192']))

            # 2. DOCUMENTS (dokument)
            if "dokument" in result_dict:
                df = result_dict["dokument"]
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO documents (document_id, title, document_type, date, riksmote, organ, status, html_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id) DO NOTHING
                    """, (row['dok_id'], row['titel'], row['doktyp'], row['datum'], row['rm'], row['organ'], row['status'], row['url']))

            # 3. VOTES (voteringar - huvudtabell)
            # Notera: Vi skapar unika röst-huvudrader först
            if "voteringar" in result_dict:
                df_votes = result_dict["voteringar"].drop_duplicates(subset=['votering_id'])
                for _, row in df_votes.iterrows():
                    cur.execute("""
                        INSERT INTO votes (vote_id, document_id, topic, riksmote, date)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (vote_id) DO NOTHING
                    """, (row['votering_id'], row['dok_id'], row['beteckning'], row['rm'], row.get('systemdatum')))

            # 4. VOTE_RESULTS (voteringar - per medlem)
            if "voteringar" in result_dict:
                df = result_dict["voteringar"]
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO vote_results (vote_id, member_id, party_id, vote)
                        VALUES (%s, %s, %s, %s)
                    """, (row['votering_id'], row['intressent_id'], row['parti'], row['rost']))

            # 5. SPEECHES (anforanden)
            if "anforanden" in result_dict:
                df = result_dict["anforanden"]
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO speeches (speech_id, member_id, party_id, riksmote, date, debate_title, speech_type, body_text, document_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (speech_id) DO NOTHING
                    """, (row['anforande_id'], row['intressent_id'], row['parti'], row['dok_rm'], 
                          row['dok_datum'], row['avsnittsrubrik'], row['kammaraktivitet'], row['anforandetext'], row['rel_dok_id']))

            # Spara alla ändringar (Commit)
            conn.commit()
            print("All data loaded successfully to Supabase/Postgres!")

def update_vote_aggregates():
    """
    Hanterar 'Extra'-steget: Beräknar yes/no/abstain rösterna i tabellen 'votes'
    efter att röstresultaten har laddats in.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE votes v
                SET 
                    yes_votes = (SELECT COUNT(*) FROM vote_results vr WHERE vr.vote_id = v.vote_id AND vr.vote = 'ja'),
                    no_votes = (SELECT COUNT(*) FROM vote_results vr WHERE vr.vote_id = v.vote_id AND vr.vote = 'nej'),
                    abstain_votes = (SELECT COUNT(*) FROM vote_results vr WHERE vr.vote_id = v.vote_id AND vr.vote = 'avstår'),
                    absent_votes = (SELECT COUNT(*) FROM vote_results vr WHERE vr.vote_id = v.vote_id AND vr.vote = 'frånvarande')
            """)
            conn.commit()
            print("Vote aggregates updated!")







