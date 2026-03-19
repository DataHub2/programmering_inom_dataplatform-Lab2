import pandas as pd
from database.load import load_to_db

# 1. Vi skapar en "låtsas-ledamot" (Mock data)
test_data = {
    "ledamoter": pd.DataFrame([{
        "intressent_id": "TEST_001",
        "tilltalsnamn": "Test",
        "efternamn": "Testsson",
        "parti": "S", # Se till att 'S' finns i din parties-tabell i Supabase!
        "valkrets": "Stockholm",
        "status": "Tjänstgörande",
        "kon": "man",
        "fodd_ar": 1980,
        "bild_url_192": "http://image.com"
    }])
}

# 2. Vi försöker köra load-funktionen
try:
    print("Försöker ansluta till Supabase...")
    load_to_db(test_data)
    print("TEST LYCKADES! Ledamoten finns nu i Supabase.")
except Exception as e:
    print(f"TEST MISSLYCKADES: {e}")