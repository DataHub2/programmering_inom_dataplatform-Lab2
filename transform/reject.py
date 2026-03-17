import pandas as pd
from clean import clean
from flag import run_flags


def build_flag_columns(
    df: pd.DataFrame,
    flags: dict[str, pd.DataFrame],
    id_col: str,
) -> pd.DataFrame:

    # Jobba på en kopia så vi inte förstör originalet
    df = df.copy()

    # Alla rader börjar med tom flagga
    df["flag"] = ""

    # Om inga flaggor finns, returnera direkt med tomma flaggkolumnen
    if not flags:
        return df

    # Slå ihop alla flaggtabeller till en enda DataFrame
    flag_df = pd.concat(flags.values(), ignore_index=True)

    # Gruppera per id så att en rad med flera flaggor får dem samlade
    # t.ex. "null_id, null_namn" istället för två separata rader
    grouped = (
        flag_df.groupby(id_col)["flag_reason"]
        .apply(lambda reasons: ", ".join(reasons))  # slå ihop till en sträng
        .reset_index()                               # gör id_col till kolumn igen
        .rename(columns={"flag_reason": "flag"})     # döp om till 'flag'
    )

    # Joina flaggorna tillbaka på hela datasetet
    # how="left" behåller alla rader — rena rader får NaN i flag-kolumnen
    df = df.merge(grouped, on=id_col, how="left", suffixes=("", "_new"))

    # Fyll i flaggkolumnen — rader utan flagga (NaN) får tom sträng
    df["flag"] = df["flag_new"].fillna("")

    # Ta bort hjälpkolumnen som merge skapade
    df = df.drop(columns=["flag_new"])

    return df


def reject(
    df_ledamoter: pd.DataFrame,
    df_voteringar: pd.DataFrame,
    df_anforanden: pd.DataFrame,
    # TODO: lägg till df_kalender: pd.DataFrame här när ID-kolumn är känd
    # TODO: lägg till df_dokument: pd.DataFrame här när ID-kolumn är känd
) -> dict[str, pd.DataFrame]:

    # Kör alla flaggkontroller
    flags = run_flags(df_ledamoter, df_voteringar, df_anforanden)
    # TODO: skicka med df_kalender och df_dokument till run_flags när de är klara

    # TODO: rost-kolumnen konverteras till True/False i clean.py men
    # flag_franvaro_topp10 letar efter strängen "frånvarande" — stämmer inte ihop.
    # Skippar denna flagga tills rost-logiken är fixad.
    flags.pop("narvaro_franvaro_topp10", None)

    # Varje dataset mappat mot sitt ID-kolumnnamn
    datasets = {
        "ledamoter":  (df_ledamoter,  "intressent_id"),
        "voteringar": (df_voteringar, "votering_id"),
        "anforanden": (df_anforanden, "anforande_id"),
        # TODO: lägg till "kalender": (df_kalender, "??_id") när ID-kolumn är känd
        # TODO: lägg till "dokument": (df_dokument, "??_id") när ID-kolumn är känd
    }

    result = {}
    for name, (df, id_col) in datasets.items():

        # Plocka ut bara flaggor som tillhör detta dataset
        relevant_flags = {
            k: v for k, v in flags.items()
            if v["flag_source"].eq(name).any()
        }

        # Lägg till flag-kolumnen på hela datasetet
        df_with_flags = build_flag_columns(df.copy(), relevant_flags, id_col)

        # Rader med tom flag-sträng är rena
        result[f"{name}_clean"] = df_with_flags[
            df_with_flags["flag"] == ""
        ].copy()

        # Rader med något i flag-kolumnen är flaggade
        result[f"{name}_flagged"] = df_with_flags[
            df_with_flags["flag"] != ""
        ].copy()

    return result


if __name__ == "__main__":
    # Läs och städa alla datasets
    df_ledamoter  = clean(pd.read_csv("data/ledamoter.csv"))
    df_voteringar = clean(pd.read_csv("data/voteringar.csv"))
    df_anforanden = clean(pd.read_csv("data/anforanden.csv"))
    # TODO: df_kalender = clean(pd.read_csv("data/kalender.csv")) när ID-kolumn är känd
    # TODO: df_dokument = clean(pd.read_csv("data/dokument.csv")) när ID-kolumn är känd

    # Kör reject-steget
    results = reject(df_ledamoter, df_voteringar, df_anforanden)
    # TODO: skicka med df_kalender och df_dokument till reject när de är klara

    # Skriv ut summering — hur många rena vs flaggade rader per dataset
    for name, df in results.items():
        print(f"{name}: {len(df)} rader")