import streamlit as st  # Streamlit for building the web app
import pandas as pd  # Pandas for data manipulation
import altair as alt  # Altair for charts
from sqlalchemy import text  # text() wraps raw SQL strings for SQLAlchemy
from utils.supabase_client import init_db  # Our database connection helper

# Page title and subtitle
st.title("Veckans riksdag")
st.write("Kommande aktiviteter i kammaren")

# Initialize the database engine
engine = init_db()

# Color map — one color per activity type, used in charts and calendar cards
AKTIVITET_FARGER = {
    "arbetsplenum":                             "#6b8fc7",
    "votering":                                 "#7fbf8f",
    "interpellationsdebatt":                    "#d97a7a",
    "frågestund":                               "#e7d488",
    "statsministerns frågestund":               "#f3eda0",
    "partiledardebatt":                         "#d37ca3",
    "återrapportering":                         "#a2c87b",
    "debatt med anledning av vårpropositionen": "#c8a87b",
    "avslutning":                               "#cccccc",
}


@st.cache_data(ttl=3600)  # Cache for 1 hour so we don't hit the database on every interaction
def hamta_kalender() -> pd.DataFrame:
    # Fetch the columns we need from the calendar table
    query = text("""
        SELECT
            "DTSTART",
            "DTEND",
            "SUMMARY",
            "CATEGORIES",
            "LOCATION"
        FROM public.calendar_raw
        ORDER BY "DTSTART" ASC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)  # Run SQL and load result into a DataFrame

    # Parse the start datetime string (e.g. "20260624t090000") into a proper datetime
    df["datum"] = pd.to_datetime(df["DTSTART"], format="%Y%m%dt%H%M%S", errors="coerce")

    # Parse the end datetime the same way
    df["slut"] = pd.to_datetime(df["DTEND"], format="%Y%m%dt%H%M%S", errors="coerce")

    # CATEGORIES looks like "kammaren,votering,debatt och beslut,kamm"
    # The second item (index 1) is the activity type we want
    df["aktivitet"] = df["CATEGORIES"].str.split(",").str[1].str.strip()

    # Format time as "HH:MM" for display
    df["tid"] = df["datum"].dt.strftime("%H:%M")

    # Format date as "YYYY-MM-DD" for grouping and display
    df["datum_str"] = df["datum"].dt.strftime("%Y-%m-%d")

    # Only keep future events — no point showing past ones
    df = df[df["datum"] >= pd.Timestamp.now()].copy()

    return df


# Load calendar data
df = hamta_kalender()


st.markdown("### Filtrera")
col1, col2 = st.columns(2)  # Two side-by-side filter controls

with col1:
    # Get all unique activity types sorted alphabetically
    aktiviteter = sorted(df["aktivitet"].dropna().unique().tolist())

    # Multiselect — user can pick one or more activity types (empty = show all)
    valda_aktiviteter = st.multiselect(
        "Aktivitetstyp",
        options=aktiviteter,
        default=[],
    )

with col2:
    # Get the earliest and latest dates in the data
    min_datum = df["datum"].min().date()
    max_datum = df["datum"].max().date()

    # Date range picker — defaults to showing the full available range
    valt_datumspann = st.date_input(
        "Datumintervall",
        value=(min_datum, max_datum),
        min_value=min_datum,
        max_value=max_datum,
    )

# Start with a copy of all data, then apply filters one by one
df_filtered = df.copy()

# Filter by activity type if user selected any
if valda_aktiviteter:
    df_filtered = df_filtered[df_filtered["aktivitet"].isin(valda_aktiviteter)]

# Filter by date range if user picked a valid range (both start and end)
if len(valt_datumspann) == 2:
    start, slut = valt_datumspann
    df_filtered = df_filtered[
        (df_filtered["datum"].dt.date >= start) &
        (df_filtered["datum"].dt.date <= slut)
    ]

st.divider()  # Horizontal line between sections


col1, col2, col3 = st.columns(3)  # Three equal columns

# Total number of events matching the current filter
col1.metric("Kommande aktiviteter", len(df_filtered))

# Number of unique days that have at least one event
col2.metric("Antal dagar", df_filtered["datum_str"].nunique())

# Number of different activity types in the filtered result
col3.metric("Aktivitetstyper", df_filtered["aktivitet"].nunique())

st.divider()


st.markdown("### Fördelning per aktivitetstyp")

# Count events per activity type and sort by most common
fordelning = (
    df_filtered.groupby("aktivitet")
    .size()
    .reset_index(name="antal")
    .sort_values("antal", ascending=False)
)

# Horizontal bar chart — one bar per activity type
chart_fordelning = (
    alt.Chart(fordelning)
    .mark_bar()
    .encode(
        x=alt.X("antal:Q", title="Antal"),  # Q = quantitative (number)
        y=alt.Y("aktivitet:N", sort="-x", title=None),  # N = nominal (category), sorted by count
        color=alt.Color(
            "aktivitet:N",
            scale=alt.Scale(
                domain=list(AKTIVITET_FARGER.keys()),  # Activity names
                range=list(AKTIVITET_FARGER.values()),  # Matching colors
            ),
            legend=None,  # No legend needed since y-axis already labels each bar
        ),
        tooltip=["aktivitet", "antal"],  # Show on hover
    )
    .properties(height=280)
    .configure_axis(labelColor="#12255C", titleColor="#12255C")
)
st.altair_chart(chart_fordelning, use_container_width=True)

st.divider()


st.markdown("### Aktiviteter per dag")

# Count events per day and activity type for a stacked bar chart
per_dag = (
    df_filtered.groupby(["datum_str", "aktivitet"])
    .size()
    .reset_index(name="antal")
)

# Stacked bar chart — x is date, y is count, color is activity type
chart_tidslinje = (
    alt.Chart(per_dag)
    .mark_bar()
    .encode(
        x=alt.X("datum_str:T", title="Datum"),  # T = temporal (date)
        y=alt.Y("antal:Q", title="Antal aktiviteter"),
        color=alt.Color(
            "aktivitet:N",
            scale=alt.Scale(
                domain=list(AKTIVITET_FARGER.keys()),
                range=list(AKTIVITET_FARGER.values()),
            ),
            legend=alt.Legend(title="Aktivitet"),
        ),
        tooltip=["datum_str", "aktivitet", "antal"],
    )
    .properties(height=300)
    .configure_axis(labelColor="#12255C", titleColor="#12255C")
)
st.altair_chart(chart_tidslinje, use_container_width=True)

st.divider()


import datetime as dt
import streamlit as st

st.markdown("### Kommande aktiviteter")


idag = dt.date.today()
start_vecka = idag - dt.timedelta(days=idag.weekday())


veckodagar = [start_vecka + dt.timedelta(days=i) for i in range(7)]


cols = st.columns(7)

vald_dag = None

for i, dag in enumerate(veckodagar):
    with cols[i]:
        label = dag.strftime("%a\n%d %b")  # t.ex. "Mon\n25 Mar"
        if st.button(label, key=str(dag)):
            vald_dag = dag


if "vald_dag" not in st.session_state:
    st.session_state.vald_dag = idag

if vald_dag:
    st.session_state.vald_dag = vald_dag

valdatum = st.session_state.vald_dag

st.markdown(f"#### {valdatum}")


df_dag = df_filtered[
    df_filtered["datum"].dt.date == valdatum
]


if df_dag.empty:
    st.info("Inga aktiviteter denna dag.")
else:
    for _, rad in df_dag.iterrows():
        farg = AKTIVITET_FARGER.get(rad["aktivitet"], "#cccccc")

        st.markdown(
            f"""
            <div style="
                border-left: 4px solid {farg};
                padding: 8px 12px;
                margin: 6px 0;
                border-radius: 0 8px 8px 0;
                background: #f9f9f9;
            ">
                <span style="font-size:13px; color:#666">{rad['tid']}</span>
                &nbsp;
                <strong>{rad['SUMMARY'].capitalize()}</strong>
                &nbsp;
                <span style="font-size:12px; color:#999">— {rad['aktivitet']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.caption("Källa: Riksdagen öppna data")