import streamlit as st
import pandas as pd
from datetime import datetime
from utils.supabase_client import init_db

st.title("Ledamöter")
st.caption("Filtrera ledamöter och utforska deras parti, kön, ålder, valkrets, röstmönster och anföranden.")

engine = init_db()



# Hjälpfunktioner

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def pick_col(df: pd.DataFrame, candidates: list[str]):
    for col in candidates:
        if col in df.columns:
            return col
    return None


@st.cache_data
def load_table(table_name: str) -> pd.DataFrame:
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    return normalize_columns(df)


def build_full_name(df: pd.DataFrame) -> pd.Series:
    first_col = pick_col(df, ["tilltalsnamn", "fornamn", "förnamn", "firstname", "first_name"])
    last_col = pick_col(df, ["efternamn", "lastname", "last_name", "surname", "namn"])

    if first_col and last_col:
        return (
            df[first_col].fillna("").astype(str).str.strip()
            + " "
            + df[last_col].fillna("").astype(str).str.strip()
        ).str.strip()

    if last_col:
        return df[last_col].fillna("").astype(str).str.strip()

    return pd.Series(["Okänt namn"] * len(df), index=df.index)


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in ["none", "nan", "null"]:
        return ""
    return text


def safe_unique(series: pd.Series):
    values = []
    for x in series.dropna().tolist():
        text = clean_text(x)
        if text:
            values.append(text)
    return sorted(list(set(values)))


def normalize_vote_value(value):
    text = clean_text(value).lower()
    mapping = {
        "ja": "Ja",
        "nej": "Nej",
        "avstår": "Avstår",
        "avstar": "Avstår",
        "frånvarande": "Frånvarande",
        "franvarande": "Frånvarande",
        "frånv.": "Frånvarande"
    }
    return mapping.get(text, text.capitalize() if text else "")



# Ladda data

try:
    members_df = load_table("members_raw")
    votes_df = load_table("votes_raw")
    speeches_df = load_table("speeches_raw")
    parties_df = load_table("parties")
    aktiva_talare_df = load_table("aktiva_talare")
except Exception as e:
    st.error(f"Kunde inte läsa data från databasen: {e}")
    st.stop()


# Identifiera kolumner

member_id_col = pick_col(members_df, ["intressent_id", "id", "person_id", "ledamot_id"])
member_gender_col = pick_col(members_df, ["kon", "kön", "gender"])
member_birth_col = pick_col(members_df, ["fodd_ar", "född_ar", "birth_year", "birthyear"])
member_constituency_col = pick_col(members_df, ["valkrets", "district", "constituency"])
member_party_col_direct = pick_col(members_df, ["parti", "party"])

members_df["namn"] = build_full_name(members_df)

if member_birth_col:
    current_year = datetime.now().year
    members_df["alder"] = current_year - pd.to_numeric(members_df[member_birth_col], errors="coerce")
else:
    members_df["alder"] = None


# Parti

members_df["parti_visning"] = ""

if member_party_col_direct:
    members_df["parti_visning"] = members_df[member_party_col_direct].apply(clean_text)

else:
    party_member_id_col = pick_col(parties_df, ["intressent_id", "id", "person_id", "ledamot_id"])
    party_name_col = pick_col(parties_df, ["parti", "party", "partibeteckning", "partinamn", "beteckning"])

    if member_id_col and party_member_id_col and party_name_col:
        party_lookup = (
            parties_df[[party_member_id_col, party_name_col]]
            .dropna(subset=[party_member_id_col])
            .drop_duplicates(subset=[party_member_id_col])
            .rename(columns={
                party_member_id_col: "__join_member_id",
                party_name_col: "parti_visning"
            })
        )

        members_df = members_df.merge(
            party_lookup,
            left_on=member_id_col,
            right_on="__join_member_id",
            how="left"
        )

        members_df["parti_visning"] = members_df["parti_visning"].apply(clean_text)

        if "__join_member_id" in members_df.columns:
            members_df = members_df.drop(columns=["__join_member_id"])

members_df["parti_visning"] = members_df["parti_visning"].replace("", "Okänt")


# Valkrets

if member_constituency_col:
    members_df["valkrets_visning"] = members_df[member_constituency_col].apply(clean_text)
else:
    party_member_id_col = pick_col(parties_df, ["intressent_id", "id", "person_id", "ledamot_id"])
    party_const_col = pick_col(parties_df, ["valkrets", "district", "constituency"])

    if member_id_col and party_member_id_col and party_const_col:
        constituency_lookup = (
            parties_df[[party_member_id_col, party_const_col]]
            .dropna(subset=[party_member_id_col])
            .drop_duplicates(subset=[party_member_id_col])
            .rename(columns={
                party_member_id_col: "__join_member_id_2",
                party_const_col: "valkrets_visning"
            })
        )

        members_df = members_df.merge(
            constituency_lookup,
            left_on=member_id_col,
            right_on="__join_member_id_2",
            how="left"
        )

        if "__join_member_id_2" in members_df.columns:
            members_df = members_df.drop(columns=["__join_member_id_2"])

members_df["valkrets_visning"] = members_df["valkrets_visning"].apply(clean_text) if "valkrets_visning" in members_df.columns else ""
members_df["valkrets_visning"] = members_df["valkrets_visning"].replace("", "Okänd")


# Kön och namn

if member_gender_col:
    members_df["kon_visning"] = members_df[member_gender_col].apply(clean_text)
else:
    members_df["kon_visning"] = "Okänd"

members_df["kon_visning"] = members_df["kon_visning"].replace("", "Okänd")
members_df["namn"] = members_df["namn"].apply(clean_text).replace("", "Okänt namn")

# Ta bort dubletter
if member_id_col:
    members_df = members_df.drop_duplicates(subset=[member_id_col])
else:
    members_df = members_df.drop_duplicates(subset=["namn"])


# Filter

st.sidebar.header("Filtrera")

search_text = st.sidebar.text_input("Sök ledamot")

party_options = ["Alla"] + safe_unique(members_df["parti_visning"])
gender_options = ["Alla"] + safe_unique(members_df["kon_visning"])
constituency_options = ["Alla"] + safe_unique(members_df["valkrets_visning"])

selected_party = st.sidebar.selectbox("Parti", party_options)
selected_gender = st.sidebar.selectbox("Kön", gender_options)
selected_constituency = st.sidebar.selectbox("Valkrets", constituency_options)

valid_ages = pd.to_numeric(members_df["alder"], errors="coerce").dropna()
if not valid_ages.empty:
    min_age_data = int(valid_ages.min())
    max_age_data = int(valid_ages.max())
    selected_age_range = st.sidebar.slider(
        "Ålder",
        min_age_data,
        max_age_data,
        (min_age_data, max_age_data)
    )
else:
    selected_age_range = None

filtered_df = members_df.copy()

if search_text:
    filtered_df = filtered_df[
        filtered_df["namn"].str.contains(search_text, case=False, na=False)
    ]

if selected_party != "Alla":
    filtered_df = filtered_df[filtered_df["parti_visning"] == selected_party]

if selected_gender != "Alla":
    filtered_df = filtered_df[filtered_df["kon_visning"] == selected_gender]

if selected_constituency != "Alla":
    filtered_df = filtered_df[filtered_df["valkrets_visning"] == selected_constituency]

if selected_age_range is not None:
    filtered_df = filtered_df[
        pd.to_numeric(filtered_df["alder"], errors="coerce").between(
            selected_age_range[0], selected_age_range[1]
        )
    ]


# KPI

c1, c2, c3 = st.columns(3)
c1.metric("Antal ledamöter", len(filtered_df))
c2.metric("Partier i urvalet", filtered_df["parti_visning"].nunique())
c3.metric("Valkretsar i urvalet", filtered_df["valkrets_visning"].nunique())


# Lista ledamöter

st.subheader("Ledamöter i urvalet")

table_df = filtered_df[["namn", "parti_visning", "kon_visning", "alder", "valkrets_visning"]].copy()
table_df = table_df.rename(columns={
    "namn": "Namn",
    "parti_visning": "Parti",
    "kon_visning": "Kön",
    "alder": "Ålder",
    "valkrets_visning": "Valkrets"
})

st.dataframe(table_df, use_container_width=True)

if filtered_df.empty:
    st.warning("Inga ledamöter matchar dina filter.")
    st.stop()


# Välj ledamot

filtered_df = filtered_df.sort_values("namn")

member_labels = filtered_df.apply(
    lambda row: f"{row['namn']} | {row['parti_visning']} | {row['valkrets_visning']}",
    axis=1
).tolist()

selected_label = st.selectbox("Välj ledamot", member_labels)
selected_row = filtered_df.iloc[member_labels.index(selected_label)]

selected_member_id = selected_row[member_id_col] if member_id_col else None
selected_member_name = selected_row["namn"]

# =========================
# Ledamotskort
# =========================
st.subheader("Information om ledamoten")

info1, info2, info3 = st.columns(3)
info1.metric("Parti", selected_row["parti_visning"])
info2.metric("Kön", selected_row["kon_visning"])
info3.metric("Ålder", "-" if pd.isna(selected_row["alder"]) else int(selected_row["alder"]))

st.markdown(
    f"""
**Namn:** {selected_row["namn"]}  
**Valkrets:** {selected_row["valkrets_visning"]}
"""
)


# Röstmönster

vote_member_id_col = pick_col(votes_df, ["intressent_id", "id", "person_id", "ledamot_id"])
vote_value_col = pick_col(votes_df, ["rost", "röst", "vote", "vote_value", "avstar_fran"])
vote_name_col = pick_col(votes_df, ["namn", "ledamot", "talare", "efternamn"])

st.subheader("Röstmönster")

person_votes = pd.DataFrame()

if selected_member_id is not None and vote_member_id_col:
    person_votes = votes_df[votes_df[vote_member_id_col] == selected_member_id].copy()
elif vote_name_col:
    surname = selected_member_name.split()[-1] if selected_member_name.strip() else selected_member_name
    person_votes = votes_df[
        votes_df[vote_name_col].astype(str).str.contains(surname, case=False, na=False)
    ].copy()

if not person_votes.empty and vote_value_col:
    person_votes["rost_visning"] = person_votes[vote_value_col].apply(normalize_vote_value)
    person_votes = person_votes[person_votes["rost_visning"] != ""]

    vote_counts = (
        person_votes["rost_visning"]
        .value_counts()
        .reset_index()
    )
    vote_counts.columns = ["Röst", "Antal"]

    chart_col, table_col = st.columns([1.2, 1])
    with chart_col:
        st.bar_chart(vote_counts.set_index("Röst"))
    with table_col:
        st.dataframe(vote_counts, use_container_width=True, hide_index=True)
else:
    st.info("Det finns inga röster att visa för den här ledamoten.")

# 
# Anföranden
# 
speech_member_id_col = pick_col(speeches_df, ["intressent_id", "id", "person_id", "ledamot_id"])
speech_text_col = pick_col(speeches_df, ["anforandetext", "anförandetext", "text", "anf_text"])
speech_title_col = pick_col(speeches_df, ["titel", "title", "rubrik"])
speech_date_col = pick_col(speeches_df, ["datum", "date", "anforandedatum"])
speech_name_col = pick_col(speeches_df, ["talare", "namn", "ledamot", "speaker"])

st.subheader("Anföranden")

person_speeches = pd.DataFrame()

if selected_member_id is not None and speech_member_id_col:
    person_speeches = speeches_df[speeches_df[speech_member_id_col] == selected_member_id].copy()
elif speech_name_col:
    surname = selected_member_name.split()[-1] if selected_member_name.strip() else selected_member_name
    person_speeches = speeches_df[
        speeches_df[speech_name_col].astype(str).str.contains(surname, case=False, na=False)
    ].copy()

if not person_speeches.empty:
    if speech_date_col and speech_date_col in person_speeches.columns:
        person_speeches[speech_date_col] = pd.to_datetime(person_speeches[speech_date_col], errors="coerce")
        person_speeches = person_speeches.sort_values(speech_date_col, ascending=False)

    if speech_text_col and speech_text_col in person_speeches.columns:
        person_speeches["text_visning"] = person_speeches[speech_text_col].apply(clean_text)
    else:
        person_speeches["text_visning"] = ""

    if speech_title_col and speech_title_col in person_speeches.columns:
        person_speeches["titel_visning"] = person_speeches[speech_title_col].apply(clean_text)
    else:
        person_speeches["titel_visning"] = ""

    if speech_name_col and speech_name_col in person_speeches.columns:
        person_speeches["talare_visning"] = person_speeches[speech_name_col].apply(clean_text)
    else:
        person_speeches["talare_visning"] = selected_member_name

    if speech_date_col and speech_date_col in person_speeches.columns:
        person_speeches["datum_visning"] = person_speeches[speech_date_col].dt.strftime("%Y-%m-%d")
        person_speeches["datum_visning"] = person_speeches["datum_visning"].fillna("")
    else:
        person_speeches["datum_visning"] = ""

    # Behåll bara rader som faktiskt har text eller titel
    person_speeches = person_speeches[
        (person_speeches["text_visning"] != "") |
        (person_speeches["titel_visning"] != "")
    ]

    if not person_speeches.empty:
        speech_table = person_speeches[["datum_visning", "titel_visning", "talare_visning"]].copy()
        speech_table = speech_table.rename(columns={
            "datum_visning": "Datum",
            "titel_visning": "Titel",
            "talare_visning": "Talare"
        })

        st.dataframe(speech_table.head(20), use_container_width=True, hide_index=True)

        st.markdown("### Senaste anförandet")
        latest = person_speeches.iloc[0]

        latest_title = latest["titel_visning"] if latest["titel_visning"] else "Anförande"
        latest_date = latest["datum_visning"] if latest["datum_visning"] else "Datum saknas"
        latest_text = latest["text_visning"]

        st.markdown(f"**{latest_title}**")
        st.write(f"**Datum:** {latest_date}")
        st.write(f"**Talare:** {latest['talare_visning']}")

        if latest_text:
            st.write(latest_text[:3000])
        else:
            st.info("Text till anförandet saknas i datan.")
    else:
        st.info("Det finns inga kompletta anföranden att visa för den här ledamoten.")
else:
    st.info("Det finns inga anföranden att visa för den här ledamoten.")


# Mest aktiva talare

st.subheader("Mest aktiva talare")

if not aktiva_talare_df.empty:
    talare_col = pick_col(aktiva_talare_df, ["talare"])
    parti_col = pick_col(aktiva_talare_df, ["parti"])
    anforanden_col = pick_col(aktiva_talare_df, ["antal_anforanden"])
    amnen_col = pick_col(aktiva_talare_df, ["antal_amnen"])

    if talare_col and parti_col and anforanden_col:
        aktiva_visning = aktiva_talare_df.copy()

        aktiva_visning["talare_visning"] = aktiva_visning[talare_col].apply(clean_text)
        aktiva_visning["parti_visning"] = aktiva_visning[parti_col].apply(clean_text)
        aktiva_visning["anforanden_visning"] = pd.to_numeric(
            aktiva_visning[anforanden_col], errors="coerce"
        ).fillna(0).astype(int)

        if amnen_col:
            aktiva_visning["amnen_visning"] = pd.to_numeric(
                aktiva_visning[amnen_col], errors="coerce"
            ).fillna(0).astype(int)
        else:
            aktiva_visning["amnen_visning"] = 0

        aktiva_visning = aktiva_visning[
            aktiva_visning["talare_visning"] != ""
        ].sort_values("anforanden_visning", ascending=False)

        top_n = st.slider("Visa topp talare", 5, 20, 10)

        top_talare = aktiva_visning.head(top_n)

        chart_df = top_talare[["talare_visning", "anforanden_visning"]].copy()
        chart_df = chart_df.rename(columns={
            "talare_visning": "Talare",
            "anforanden_visning": "Antal anföranden"
        })

        st.bar_chart(chart_df.set_index("Talare"))

        table_df = top_talare[[
            "talare_visning",
            "parti_visning",
            "anforanden_visning",
            "amnen_visning"
        ]].copy()

        table_df = table_df.rename(columns={
            "talare_visning": "Talare",
            "parti_visning": "Parti",
            "anforanden_visning": "Antal anföranden",
            "amnen_visning": "Antal ämnen"
        })

        st.dataframe(table_df, use_container_width=True, hide_index=True)
    else:
        st.info("Kunde inte läsa kolumnerna i aktiva_talare.")
else:
    st.info("Ingen data hittades i aktiva_talare.")