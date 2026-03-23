import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from supabase import create_client
import streamlit as st

load_dotenv()  # load .env file

@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

@st.cache_resource
def init_db():
    db_url = os.getenv("SUPABASE_DB_URL")
    return create_engine(db_url, pool_pre_ping=True)