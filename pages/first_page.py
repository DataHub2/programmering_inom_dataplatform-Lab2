import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import altair as alt

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
        return pd.read_sql(query, conn)

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

st.text("Datan presenterad här är hur det såg ut under senaste riksmötet")
col1, col2, col3 = st.columns(3)
col1.metric("Ledamöter", f"{int(kpi['antal_ledamoter'])}")
col2.metric("Partier", int(kpi['antal_partier']))
col3.metric("Talare", int(kpi['antal_talare']))

@st.cache_data(ttl=3600)
def antal_narvarande_per_parti():
    query = text("""
        SELECT 
            parti, 
            COUNT(DISTINCT intressent_id) AS antal_ledamoter
        FROM public.votes_raw
        GROUP BY parti
        ORDER BY antal_ledamoter DESC;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

st.space(size="medium")

# Hämta data
df = antal_narvarande_per_parti()
df['parti'] = df['parti'].str.upper()

# Definiera partifärger (exempel på riksdagspartiernas färger)
parti_colors = {
    "S": "#d97a7a",   # mild röd
    "M": "#6b8fc7",   # ljusblå
    "SD": "#5a6b91",  # mörkare blå
    "C": "#7fbf8f",   # mjuk grön
    "V": "#d37ca3",   # mild rosa
    "KD": "#e7d488",  # mjuk gul
    "L": "#f3eda0",   # ljusgul
    "MP": "#a2c87b",  # mild grön
    "-": "#FFFAFA"
}

# Horisontell barchart
chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('antal_ledamoter:Q', title='Antal ledamöter'),
    y=alt.Y('parti:N', sort='-x', title='Parti'),  # partier på y-axeln
    color=alt.Color('parti:N', scale=alt.Scale(domain=list(parti_colors.keys()), range=list(parti_colors.values()))),
    tooltip=['parti', 'antal_ledamoter']
).properties(
    width=700,
    height=400,
    title='Antal närvarande ledamöter per parti'
).configure_axis(
    labelColor="#12255C",   # färg på axeltext
    titleColor="#12255C"    # färg på axeltitlar
).configure_title(
    color="#12255C"         # färg på diagramtitel
)


st.altair_chart(chart, use_container_width=True)

# Funktion för att hämta könsfördelning per parti från din databas
@st.cache_data(ttl=3600)
def konsfordelning_per_parti():
    query = text("""
        SELECT parti, kon, COUNT(DISTINCT intressent_id) AS antal_ledamoter
        FROM public.votes_raw
        GROUP BY parti, kon
        ORDER BY parti, kon;
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        df['parti'] = df['parti'].str.upper()  # standardisera partinamn
        return df

# Hämta data
df = konsfordelning_per_parti()

# Mutade färger för kön
kon_colors = {
    "man": "#6b8fc7",   # mild blå för män
    "kvinna": "#d97a7a",   # mild rosa för kvinnor
}

# Skapa horisontell stacked bar chart
chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('antal_ledamoter:Q', title='Antal ledamöter'),
    y=alt.Y('parti:N', sort='-x', title='Parti'),
    color=alt.Color('kon:N', scale=alt.Scale(domain=list(kon_colors.keys()),
                                             range=list(kon_colors.values())),
                    legend=alt.Legend(title="Kön")),
    tooltip=['parti', 'kon', 'antal_ledamoter']
).properties(
    width=700,
    height=400,
    title='Könsfördelning per parti'
).configure_axis(
    labelColor="#12255C",   # färg på axeltext
    titleColor="#12255C"    # färg på axeltitlar
).configure_title(
    color="#12255C"         # färg på diagramtitel
)

st.altair_chart(chart, use_container_width=True)


st.caption("Källa: Riksdagen")