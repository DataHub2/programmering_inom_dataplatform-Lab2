import os
from dotenv import load_dotenv
from supabase import create_client
import streamlit as st

load_dotenv()  # load .env file

@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)