import streamlit as st
from sqlalchemy import text
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


@st.cache_data(ttl=300)
def hamta_pipeline_status():
    query = text("""
        SELECT
            source,
            status,
            records_inserted,
            started_at,
            finished_at,
            duration_ms,
            error_message
        FROM public.pipeline_logs
        WHERE started_at = (
            SELECT MAX(started_at)
            FROM public.pipeline_logs pl2
            WHERE pl2.source = pipeline_logs.source
        )
        ORDER BY source
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


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
        df['parti'] = df['parti'].str.upper()
        return df


# --- Styling ---
st.markdown("""
<style>
[data-testid="stMetric"] {
    background-color: #567AC8;
    padding: 15px;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

# --- KPI-rad ---
kpi = hamta_kpier()
st.text("Datan presenterad här är hur det såg ut under senaste riksmötet")
col1, col2, col3 = st.columns(3)
col1.metric("Ledamöter", f"{int(kpi['antal_ledamoter'])}")
col2.metric("Partier", int(kpi['antal_partier']))
col3.metric("Talare", int(kpi['antal_talare']))

# --- Pipeline-status ---
st.divider()
with st.expander("Pipeline-status — senaste datahämtning"):
    try:
        df_status = hamta_pipeline_status()
        if df_status.empty:
            st.info("Ingen loggdata ännu — kör load.py för att populera pipeline_logs.")
        else:
            for _, rad in df_status.iterrows():
                source       = rad["source"]
                status       = rad["status"]
                antal        = int(rad["records_inserted"]) if pd.notna(rad["records_inserted"]) else 0
                started      = str(rad["started_at"])[:19].replace("T", " ") if pd.notna(rad["started_at"]) else "—"
                duration     = f'{int(rad["duration_ms"])} ms' if pd.notna(rad["duration_ms"]) else "—"
                error        = rad["error_message"] if pd.notna(rad["error_message"]) else None

                if status == "success":
                    st.success(f"**{source}** — {antal:,} rader · {started} · {duration}")
                else:
                    st.error(f"**{source}** — fel vid senaste körning: {error}")
    except Exception as e:
        st.error(f"Kunde inte hämta pipeline-status: {e}")

st.divider()

# --- Diagram: ledamöter per parti ---
parti_colors = {
    "S":  "#d97a7a",
    "M":  "#6b8fc7",
    "SD": "#5a6b91",
    "C":  "#7fbf8f",
    "V":  "#d37ca3",
    "KD": "#e7d488",
    "L":  "#f3eda0",
    "MP": "#a2c87b",
    "-":  "#FFFAFA",
}

df = antal_narvarande_per_parti()
df['parti'] = df['parti'].str.upper()

chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('antal_ledamoter:Q', title='Antal ledamöter'),
    y=alt.Y('parti:N', sort='-x', title='Parti'),
    color=alt.Color('parti:N', scale=alt.Scale(
        domain=list(parti_colors.keys()),
        range=list(parti_colors.values())
    )),
    tooltip=['parti', 'antal_ledamoter']
).properties(
    width=700,
    height=400,
    title='Antal närvarande ledamöter per parti'
).configure_axis(
    labelColor="#12255C",
    titleColor="#12255C"
).configure_title(
    color="#12255C"
)

st.altair_chart(chart, use_container_width=True)

# --- Diagram: könsfördelning per parti ---
df = konsfordelning_per_parti()

kon_colors = {
    "man":    "#6b8fc7",
    "kvinna": "#d97a7a",
}

chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('antal_ledamoter:Q', title='Antal ledamöter'),
    y=alt.Y('parti:N', sort='-x', title='Parti'),
    color=alt.Color('kon:N', scale=alt.Scale(
        domain=list(kon_colors.keys()),
        range=list(kon_colors.values())
    ), legend=alt.Legend(title="Kön")),
    tooltip=['parti', 'kon', 'antal_ledamoter']
).properties(
    width=700,
    height=400,
    title='Könsfördelning per parti'
).configure_axis(
    labelColor="#12255C",
    titleColor="#12255C"
).configure_title(
    color="#12255C"
)

st.altair_chart(chart, use_container_width=True)

# --- Ordbok ---
st.divider()
with st.expander("Ordbok — riksdagstermer förklarade"):
    st.markdown("""
    | Term | Förklaring |
    |---|---|
    | **Anförande** | Ett tal som en ledamot håller i kammaren under en debatt |
    | **Replik** | Ett kort svar på ett anförande, max 1 minut |
    | **Votering** | Omröstning där ledamöterna trycker Ja, Nej eller Avstår |
    | **Betänkande** | Utskottets sammanfattning och förslag i en fråga, t.ex. AU10 |
    | **Utskott** | Arbetsgrupp som bereder ärenden innan de tas upp i kammaren |
    | **Kammaren** | Riksdagens plenisal där alla 349 ledamöter samlas för debatt och beslut |
    | **Riksmöte** | Riksdagens arbetsår, löper från september till juni, t.ex. 2025/26 |
    | **Proposition** | Förslag från regeringen till riksdagen om ny lag eller ändring |
    | **Motion** | Förslag från en eller flera ledamöter, ofta som svar på en proposition |
    | **Bifall** | Riksdagen röstar ja — förslaget går igenom |
    | **Avslag** | Riksdagen röstar nej — förslaget faller |
    | **Bordläggning** | Beslut skjuts upp till ett senare sammanträde |
    | **Interpellation** | En skriftlig fråga från en ledamot till en minister, besvaras i kammaren |
    | **Kvittning** | Överenskommelse där en frånvarande ledamot från ett parti matchas mot en frånvarande från ett annat, så att styrkeförhållandet i voteringen inte påverkas |
    | **Valkrets** | Det geografiska område en ledamot är vald från |
    | **Ersättare** | Ledamot som tillfälligt träder in när en ordinarie ledamot är ledig |
    """)

st.caption("Källa: Riksdagen")