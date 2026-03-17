import pandas as pd
from clean import clean
from flag import run_flags


def add_flags(
    df: pd.DataFrame,
    flags: dict[str, pd.DataFrame],
    id_col: str,
) -> pd.DataFrame:
    # Jobba på en kopia
    df = df.copy()

    # Börja med tom flaggkolumn på alla rader
    df["flag_reason"] = ""

    # Om inga flaggor finns, returnera direkt
    if not flags:
        return df

    # Slå ihop alla flaggtabeller till en
    flag_df = pd.concat(flags.values(), ignore_index=True)

    # Gruppera per id — en rad kan ha flera flaggor t.ex. "null_id, null_namn"
    grouped = (
        flag_df.groupby(id_col)["flag_reason"]
        .apply(lambda x: ", ".join(x))
        .reset_index()
    )

    # Joina flaggorna på hela datasetet
    df = df.merge(grouped, on=id_col, how="left", suffixes=("", "_new"))

    # Fyll i flaggkolumnen — rader utan flagga får tom sträng
    df["flag_reason"] = df["flag_reason_new"].fillna("")

    # Ta bort hjälpkolumnen
    df = df.drop(columns=["flag_reason_new"])

    return df

def reject_ledamoter(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[
        "hangar_guid",           # internt system-ID
        "sourceid",              # internt system-ID
        "hangar_id",             # internt system-ID
        "bild_url_80",           # bildurl
        "bild_url_192",          # bildurl
        "bild_url_max",          # bildurl
        "person_url_xml",        # XML-url
        "sorteringsnamn",        # redundant — finns i efternamn + tilltalsnamn
        "personuppdrag.uppdrag", # stor JSON-blob
        "personuppgift.uppgift", # stor JSON-blob
    ])

def reject_voteringar(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[
        "hangar_id",        # internt system-ID
        "votering_url_xml", # XML-url
        "systemdatum",      # internt
        "iort",             # nästan alltid tomt
    ])


def reject_anforanden(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[
        "dok_hangar_id",      # internt system-ID
        "anforande_url_xml",  # XML-url
        "anforande_url_html", # HTML-url
        "protokoll_url_www",  # url
        "systemdatum",        # internt
        "systemnyckel",       # internt
    ])

def transform(
    df_ledamoter: pd.DataFrame,
    df_voteringar: pd.DataFrame,
    df_anforanden: pd.DataFrame,
    # TODO: lägg till df_kalender: pd.DataFrame när flag.py har flaggar för kalender
    # TODO: lägg till df_dokument: pd.DataFrame när flag.py har flaggar för dokument
) -> dict[str, pd.DataFrame]:

    # Hämta alla flaggor från flag.py
    flags = run_flags(df_ledamoter, df_voteringar, df_anforanden)
    # TODO: skicka med df_kalender och df_dokument till run_flags när de är klara

    # TODO: ta bort när rost är fixad i clean.py
    flags.pop("narvaro_franvaro_topp10", None)

    # Varje dataset med sitt ID-kolumnnamn
    datasets = {
        "ledamoter":  (df_ledamoter,  "intressent_id"),
        "voteringar": (df_voteringar, "votering_id"),
        "anforanden": (df_anforanden, "anforande_id"),
        # TODO: lägg till "kalender": (df_kalender, "UID") när flag.py är klar
        # TODO: lägg till "dokument": (df_dokument, "id") när flag.py är klar
    }

    result = {}
    for name, (df, id_col) in datasets.items():

        # Plocka ut bara flaggor som tillhör detta dataset
        relevant_flags = {
            k: v for k, v in flags.items()
            if v["flag_source"].eq(name).any()
        }

        #lägg till flag_reason på datasetet
        df = add_flags(df, relevant_flags, id_col)

        #ta bort onödiga kolumner per dataset
        if name == "ledamoter":
            df = reject_ledamoter(df)
        elif name == "voteringar":
            df = reject_voteringar(df)
        elif name == "anforanden":
            df = reject_anforanden(df)

        result[name] = df

    return result


if __name__ == "__main__":
    # Läs och städa alla datasets
    df_ledamoter  = clean(pd.read_csv("data/ledamoter.csv"))
    df_voteringar = clean(pd.read_csv("data/voteringar.csv"))
    df_anforanden = clean(pd.read_csv("data/anforanden.csv"))
    # TODO: df_kalender = clean(pd.read_csv("data/kalender.csv")) när flag.py är klar
    # TODO: df_dokument = clean(pd.read_csv("data/dokument.csv")) när flag.py är klar

    # Kör transform
    result = transform(df_ledamoter, df_voteringar, df_anforanden)
    # TODO: skicka med df_kalender och df_dokument till transform när de är klara

    # Skriv ut summering
    for name, df in result.items():
        flagged_count = (df["flag_reason"] != "").sum()
        print(f"{name}: {len(df)} rader, {flagged_count} flaggade")
        print(f"  kolumner: {df.columns.tolist()}")
        print()