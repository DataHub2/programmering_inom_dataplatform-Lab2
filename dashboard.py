import os
from dotenv import load_dotenv
from supabase import create_client
import streamlit as st

load_dotenv()  # laddar in .env filen

@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

# title
st.title("riksdags_data")
st.write("här kan man skriva något")



st.caption("Källa: Riksdagen")

