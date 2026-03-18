import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Laddar variablerna från .env-fil
load_dotenv()

# 2. Hämta värdena exakt som de heter i din .env
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB")
port = os.getenv("POSTGRES_PORT", "5432")

# 3. SMART HOST-HANTERING:
# Om du kör 'pytest' eller python lokalt på Macen, använd 'localhost'.
# Om koden körs i Docker, använd 'db' (som står i din .env).
host = os.getenv("POSTGRES_HOST", "db")
if os.getenv("KÖRS_LOKALT") == "true":
    host = "localhost"

# 4. Skapa anslutningssträngen (Connection String)
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

# 5. Starta motorn
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() 