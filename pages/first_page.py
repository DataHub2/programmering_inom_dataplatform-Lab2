import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from streamlit import title

from utils.supabase_client import init_db

st.title("Riksdagen i siffror")
st.write("Ledamöter, röster och debatter — samlat i en vy")

engine = init_db()

@st.cache_data(ttl=3600)
def hamta_kpier():
    query = text("""
       SELECT
            (SELECT COUNT(DISTINCT intressent_id) FROM public.members_raw) AS antal_ledamoter,
            (SELECT COUNT(DISTINCT parti) FROM public.members_raw WHERE parti != '-') AS antal_partier,
            (SELECT COUNT(DISTINCT talare) FROM public.speeches_raw) AS antal_talare,
            (SELECT ROUND(COUNT(*) FILTER (WHERE rost = 'Frånvarande') * 100.0 / COUNT(*), 1)
             FROM public.votes_raw WHERE parti != '-') AS franvaro_pct
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn).iloc[0]

st.markdown("""
<style>
[data-testid="stMetric"] {
    background-color: #567AC8;
    padding: 15px;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

kpi = hamta_kpier()

st.text("senaste riksmötet")
col1, col2, col3 = st.columns(3)
col1.metric("Ledamöter", f"{int(kpi['antal_ledamoter'])}")
col2.metric("Partier", int(kpi['antal_partier']))
col3.metric("Talare", int(kpi['antal_talare']))




st.caption("Källa: Riksdagen")