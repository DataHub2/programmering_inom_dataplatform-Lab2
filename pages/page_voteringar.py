import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine, text
from utils.supabase_client import init_db

st.title("Voteringar")
st.write("Hur röstade partierna i olika frågor?")

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
def hamta_voteringar() -> pd.DataFrame:
    query = text("""
        SELECT
            votering_id,
            beteckning,
            parti,
            rost,
            namn,
            intressent_id
        FROM public.votes_raw
        WHERE parti != '-'
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        df["parti"] = df["parti"].str.upper()
        df["rost"] = df["rost"].str.lower()
        return df


@st.cache_data(ttl=3600)
def hamta_beteckningar() -> list[str]:
    query = text("SELECT DISTINCT beteckning FROM public.votes_raw ORDER BY beteckning")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [r[0] for r in result if r[0]]


df = hamta_voteringar()
beteckningar = hamta_beteckningar()

# --- Filter ---
st.markdown("### Filtrera")
col1, col2 = st.columns(2)

with col1:
    vald_beteckning = st.selectbox(
        "Välj fråga (beteckning)",
        options=["Alla"] + beteckningar,
    )

with col2:
    valda_partier = st.multiselect(
        "Filtrera på parti",
        options=sorted(df["parti"].unique().tolist()),
        default=[],
    )

# Tillämpa filter
df_filtered = df.copy()
if vald_beteckning != "Alla":
    df_filtered = df_filtered[df_filtered["beteckning"] == vald_beteckning]
if valda_partier:
    df_filtered = df_filtered[df_filtered["parti"].isin(valda_partier)]

st.divider()

# --- KPI-rad ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Totalt röster", len(df_filtered))
col2.metric("Ja", len(df_filtered[df_filtered["rost"] == "ja"]))
col3.metric("Nej", len(df_filtered[df_filtered["rost"] == "nej"]))
col4.metric("Frånvarande", len(df_filtered[df_filtered["rost"] == "frånvarande"]))

st.divider()

# --- Röstfördelning per parti ---
st.markdown("### Röstfördelning per parti")

rostfordelning = (
    df_filtered.groupby(["parti", "rost"])
    .size()
    .reset_index(name="antal")
)

rost_colors = {
    "ja":          "#7fbf8f",
    "nej":         "#d97a7a",
    "avstår":      "#e7d488",
    "frånvarande": "#cccccc",
}

chart_rost = (
    alt.Chart(rostfordelning)
    .mark_bar()
    .encode(
        x=alt.X("antal:Q", title="Antal röster"),
        y=alt.Y("parti:N", sort="-x", title="Parti"),
        color=alt.Color(
            "rost:N",
            scale=alt.Scale(
                domain=list(rost_colors.keys()),
                range=list(rost_colors.values()),
            ),
            legend=alt.Legend(title="Röst"),
        ),
        tooltip=["parti", "rost", "antal"],
    )
    .properties(width=700, height=350, title="Röstfördelning per parti")
    .configure_axis(labelColor="#12255C", titleColor="#12255C")
    .configure_title(color="#12255C")
)

st.altair_chart(chart_rost, use_container_width=True)

# --- Enighet inom parti ---
st.markdown("### Enighet inom parti")
st.caption("Andel ledamöter som röstade på majoritetens linje per parti")

def berakna_enighet(df: pd.DataFrame) -> pd.DataFrame:
    result = []
    for parti, grp in df.groupby("parti"):
        totalt = len(grp)
        if totalt == 0:
            continue
        vanligast = grp["rost"].value_counts().idxmax()
        antal_eniga = grp["rost"].value_counts().max()
        enighet_pct = round(antal_eniga / totalt * 100, 1)
        result.append({
            "parti": parti,
            "vanligaste_rost": vanligast,
            "enighet_%": enighet_pct,
        })
    return pd.DataFrame(result).sort_values("enighet_%", ascending=False)

df_enighet = berakna_enighet(df_filtered)

chart_enighet = (
    alt.Chart(df_enighet)
    .mark_bar()
    .encode(
        x=alt.X("enighet_%:Q", title="Enighet (%)", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("parti:N", sort="-x", title="Parti"),
        color=alt.Color(
            "parti:N",
            scale=alt.Scale(
                domain=list(PARTI_FARGER.keys()),
                range=list(PARTI_FARGER.values()),
            ),
            legend=None,
        ),
        tooltip=["parti", "vanligaste_rost", "enighet_%"],
    )
    .properties(width=700, height=300, title="Intern enighet per parti (%)")
    .configure_axis(labelColor="#12255C", titleColor="#12255C")
    .configure_title(color="#12255C")
)

st.altair_chart(chart_enighet, use_container_width=True)

# --- Närvaro per ledamot ---
st.markdown("### Närvaro per ledamot")
st.caption("Andel voteringar där ledamoten var närvarande (ej frånvarande)")

narvaro = (
    df_filtered.groupby(["namn", "parti"])
    .apply(lambda g: round((g["rost"] != "frånvarande").sum() / len(g) * 100, 1))
    .reset_index(name="narvaro_%")
    .sort_values("narvaro_%", ascending=True)
)

col_filter, _ = st.columns([2, 3])
with col_filter:
    visa_antal = st.slider("Visa antal ledamöter", min_value=5, max_value=50, value=20)

narvaro_urval = narvaro.head(visa_antal)

chart_narvaro = (
    alt.Chart(narvaro_urval)
    .mark_bar()
    .encode(
        x=alt.X("narvaro_%:Q", title="Närvaro (%)", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("namn:N", sort="x", title="Ledamot"),
        color=alt.Color(
            "parti:N",
            scale=alt.Scale(
                domain=list(PARTI_FARGER.keys()),
                range=list(PARTI_FARGER.values()),
            ),
            legend=alt.Legend(title="Parti"),
        ),
        tooltip=["namn", "parti", "narvaro_%"],
    )
    .properties(width=700, height=max(300, visa_antal * 18), title="Närvaro per ledamot (%)")
    .configure_axis(labelColor="#12255C", titleColor="#12255C")
    .configure_title(color="#12255C")
)

st.altair_chart(chart_narvaro, use_container_width=True)

st.caption("Källa: Riksdagen öppna data")