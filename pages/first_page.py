import streamlit as st
from utils.supabase_client import init_supabase
from sqlalchemy import create_engine, text
import pandas as pd
from utils.supabase_client import init_db
import os

st.title("Riksdagen i siffror")
st.write("Ledamöter, röster och debatter — samlat i en vy")


engine = init_db()

@st.cache_data(ttl=3600)
def hamta_aktiva_talare():
    query = text("""
        SELECT
            talare,
            parti,
            COUNT(*) AS antal_anforanden,
            COUNT(DISTINCT avsnittsrubrik) AS antal_amnen
        FROM speeches_raw
        GROUP BY talare, parti
        ORDER BY antal_anforanden DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

df_talare = hamta_aktiva_talare()

# Filter i Streamlit
partier = sorted(df_talare["parti"].unique())
valt_parti = st.selectbox("Filtrera på parti", ["Alla"] + partier)

if valt_parti != "Alla":
    df_filtrerad = df_talare[df_talare["parti"] == valt_parti]
else:
    df_filtrerad = df_talare

st.dataframe(df_filtrerad)


st.caption("Källa: Riksdagen")
