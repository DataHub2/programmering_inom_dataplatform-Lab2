import pandas as pd
from .database import engine # Vi importerar 'engine' (sladden) från filen bredvid

def load_to_db(df: pd.DataFrame, table_name: str):
    """
    Den här funktionen tar en färdigbehandlad DataFrame och sparar den i SQL.
    - table_name: Namnet på tabellen i databasen (t.ex. 'voteringar' eller 'ledamoter').
    """
    
    # Om vår DataFrame är tom finns det ingen anledning att köra databasen.
    if df.empty:
        print(f"⚠️ Ingen data att ladda för tabellen '{table_name}'. Hoppar över.")
        return

    try:
        # .to_sql är en Pandas-funktion som gör grovjobbet.
        # if_exists='append' betyder: "Om tabellen finns, lägg till ny data längst ner".
        # index=False betyder: "Spara inte Pandas egna radnummer i databasen".
        df.to_sql(table_name, engine, if_exists="append", index=False)
        
        print(f"✅ Success: {len(df)} rader har sparats i tabellen '{table_name}'.")
        
    except Exception as e:
        # Om något går fel (t.ex. fel datatyper eller låst fil) skriver vi ut felet här.
        print(f"❌ Error vid laddning till databasen ({table_name}): {e}")
