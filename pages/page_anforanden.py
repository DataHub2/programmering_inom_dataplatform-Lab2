import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine, text
from utils.supabase_client import init_db

st.title("Anföranden")
st.write("Sök och filtrera riksdagsdebatter")

engine = init_db()

PARTI_FARGER = {
    "S":  "#d97a7a",
    "M":  "#6b8fc7",
    "SD": "#5a6b91",
    "C":  "#7fbf8f",
    "V":  "#d37ca3",
    "KD": "#e7d488",
    "L":  "#f3eda0",
    "MP": "#a2c87b",
    "-":  "#cccccc",
}


@st.cache_data(ttl=3600)
def hamta_anforanden() -> pd.DataFrame:
    query = text("""
        SELECT
            anforande_id,
            talare,
            parti,
            avsnittsrubrik,
            kammaraktivitet,
            replik,
            dok_datum,
            anforandetext
        FROM public.speeches_raw
        ORDER BY dok_datum DESC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        df["parti"] = df["parti"].str.upper()
        df["talare"] = df["talare"].str.title()
        df["avsnittsrubrik"] = df["avsnittsrubrik"].str.title()
        df["dok_datum"] = pd.to_datetime(df["dok_datum"], errors="coerce")
        return df


df = hamta_anforanden()

# --- Filter ---
st.markdown("### Filtrera")
col1, col2, col3 = st.columns(3)

with col1:
    valda_partier = st.multiselect(
        "Parti",
        options=sorted(df["parti"].dropna().unique().tolist()),
        default=[],
    )

with col2:
    talare_lista = sorted(df["talare"].dropna().unique().tolist())
    vald_talare = st.selectbox("Talare", options=["Alla"] + talare_lista)

with col3:
    aktiviteter = sorted(df["kammaraktivitet"].dropna().unique().tolist())
    vald_aktivitet = st.selectbox("Typ av debatt", options=["Alla"] + aktiviteter)

sokterm = st.text_input("Sök på ämne", placeholder="t.ex. klimat, skatt, försvar...")

if not df["dok_datum"].isna().all():
    min_datum = df["dok_datum"].min().date()
    max_datum = df["dok_datum"].max().date()
    datum_range = st.date_input(
        "Datumintervall",
        value=(min_datum, max_datum),
        min_value=min_datum,
        max_value=max_datum,
    )
else:
    datum_range = None

# Tillämpa filter
df_filtered = df.copy()

if valda_partier:
    df_filtered = df_filtered[df_filtered["parti"].isin(valda_partier)]
if vald_talare != "Alla":
    df_filtered = df_filtered[df_filtered["talare"] == vald_talare]
if vald_aktivitet != "Alla":
    df_filtered = df_filtered[df_filtered["kammaraktivitet"] == vald_aktivitet]
if sokterm:
    df_filtered = df_filtered[
        df_filtered["avsnittsrubrik"].str.contains(sokterm, case=False, na=False)
    ]
if datum_range and len(datum_range) == 2:
    df_filtered = df_filtered[
        (df_filtered["dok_datum"].dt.date >= datum_range[0]) &
        (df_filtered["dok_datum"].dt.date <= datum_range[1])
    ]

st.divider()

# --- KPI-rad ---
col1, col2, col3 = st.columns(3)
col1.metric("Anföranden", len(df_filtered))
col2.metric("Unika talare", df_filtered["talare"].nunique())
col3.metric("Ämnen", df_filtered["avsnittsrubrik"].nunique())

st.divider()

# --- Anföranden per parti ---
st.markdown("### Anföranden per parti")

per_parti = (
    df_filtered.groupby("parti")
    .size()
    .reset_index(name="antal")
    .sort_values("antal", ascending=False)
)

chart_parti = (
    alt.Chart(per_parti)
    .mark_bar()
    .encode(
        x=alt.X("antal:Q", title="Antal anföranden"),
        y=alt.Y("parti:N", sort="-x", title="Parti"),
        color=alt.Color(
            "parti:N",
            scale=alt.Scale(
                domain=list(PARTI_FARGER.keys()),
                range=list(PARTI_FARGER.values()),
            ),
            legend=None,
        ),
        tooltip=["parti", "antal"],
    )
    .properties(width=700, height=300, title="Antal anföranden per parti")
    .configure_axis(labelColor="#12255C", titleColor="#12255C")
    .configure_title(color="#12255C")
)

st.altair_chart(chart_parti, use_container_width=True)

# --- Populäraste ämnena ---
st.markdown("### Mest debatterade ämnen")

amnen = (
    df_filtered["avsnittsrubrik"]
    .dropna()
    .value_counts()
    .head(10)
    .reset_index()
)
amnen.columns = ["ämne", "antal"]

chart_amnen = (
    alt.Chart(amnen)
    .mark_bar()
    .encode(
        x=alt.X("antal:Q", title="Antal anföranden"),
        y=alt.Y("ämne:N", sort="-x", title="Ämne"),
        tooltip=["ämne", "antal"],
        color=alt.value("#6b8fc7"),
    )
    .properties(width=700, height=320, title="Topp 10 mest debatterade ämnen")
    .configure_axis(labelColor="#12255C", titleColor="#12255C")
    .configure_title(color="#12255C")
)

st.altair_chart(chart_amnen, use_container_width=True)

# --- Anförandelista ---
st.markdown("### Anförandelista")
st.caption(f"Visar {min(len(df_filtered), 100)} av {len(df_filtered)} anföranden")

visa_cols = ["dok_datum", "talare", "parti", "avsnittsrubrik", "kammaraktivitet", "replik"]
visa_cols = [c for c in visa_cols if c in df_filtered.columns]

st.dataframe(
    df_filtered[visa_cols]
    .head(100)
    .rename(columns={
        "dok_datum":       "Datum",
        "talare":          "Talare",
        "parti":           "Parti",
        "avsnittsrubrik":  "Ämne",
        "kammaraktivitet": "Typ",
        "replik":          "Replik",
    }),
    use_container_width=True,
    hide_index=True,
)

st.caption("Källa: Riksdagen öppna data")