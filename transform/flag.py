import pandas as pd

# Runs after the cleaning step. Takes cleaned DataFrames as input and returns
# a dict of flag tables to be passed on to the reject handler.


def flag_null_id(df: pd.DataFrame, id_col: str, source: str) -> pd.DataFrame:
    """
    Flags rows where the ID column is null, NaN, or an empty string.

    Args:
        df:      Cleaned DataFrame
        id_col:  Name of the ID column (e.g. 'intressent_id', 'votering_id')
        source:  Source name for traceability (e.g. 'ledamoter', 'voteringar')

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    mask = df[id_col].isna() | (df[id_col].astype(str).str.strip() == "")
    flagged = df[mask].copy()
    flagged["flag_reason"] = "null_id"
    flagged["flag_source"] = source
    flagged["flag_col"] = id_col
    return flagged


def flag_null_namn(df: pd.DataFrame, namn_cols: list[str], source: str) -> pd.DataFrame:
    """
    Flags rows where ALL name columns are null or empty.
    A row is only flagged if every name column is missing — one is enough to pass.

    Args:
        df:         Cleaned DataFrame
        namn_cols:  Name columns to check, e.g. ['tilltalsnamn', 'efternamn']
        source:     Source name for traceability

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    existing_cols = [c for c in namn_cols if c in df.columns]
    if not existing_cols:
        return pd.DataFrame()  # no name columns present, nothing to flag

    mask = df[existing_cols].apply(
        lambda col: col.isna() | (col.astype(str).str.strip() == "")
    ).all(axis=1)

    flagged = df[mask].copy()
    flagged["flag_reason"] = "null_namn"
    flagged["flag_source"] = source
    flagged["flag_col"] = ", ".join(existing_cols)
    return flagged


def flag_franvaro_topp10(df_voteringar: pd.DataFrame) -> pd.DataFrame:
    """
    Flags the top 10 members with the most absences and the top 10 with the
    fewest absences (highest attendance) in the voting data.
    Both groups are returned in the same table with separate flag_reason values.

    Args:
        df_voteringar:  Cleaned voteringar DataFrame

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    # Absence count per member
    franvaro = (
        df_voteringar[df_voteringar["rost"] == "frånvarande"]
        .groupby("intressent_id")
        .size()
        .reset_index(name="antal_franvaro")
        .sort_values("antal_franvaro", ascending=False)
    )

    topp10_franvaro_ids = franvaro.head(10)["intressent_id"].tolist()

    # Attendance rate per member (lowest absence share = highest attendance)
    totalt = (
        df_voteringar
        .groupby("intressent_id")
        .size()
        .reset_index(name="totalt")
    )
    merged = totalt.merge(franvaro, on="intressent_id", how="left")
    merged["antal_franvaro"] = merged["antal_franvaro"].fillna(0)
    merged["narvaro_andel"] = 1 - (merged["antal_franvaro"] / merged["totalt"])
    topp10_narvaro_ids = (
        merged.sort_values("narvaro_andel", ascending=False)
        .head(10)["intressent_id"]
        .tolist()
    )

    # Build flag table
    franvaro_rows = df_voteringar[
        df_voteringar["intressent_id"].isin(topp10_franvaro_ids)
        & (df_voteringar["rost"] == "frånvarande")
    ].copy()
    franvaro_rows["flag_reason"] = "topp10_franvaro"

    narvaro_rows = df_voteringar[
        df_voteringar["intressent_id"].isin(topp10_narvaro_ids)
    ].copy()
    narvaro_rows["flag_reason"] = "topp10_narvaro"

    flagged = pd.concat([franvaro_rows, narvaro_rows], ignore_index=True)
    flagged["flag_source"] = "voteringar"
    flagged["flag_col"] = "rost"
    return flagged


def run_flags(
    df_ledamoter: pd.DataFrame,
    df_voteringar: pd.DataFrame,
    df_anforanden: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """
    Runs all flag checks and returns a dict of flag tables.
    Add new flag calls here as the pipeline grows.

    Args:
        df_ledamoter:   Cleaned ledamoter DataFrame
        df_voteringar:  Cleaned voteringar DataFrame
        df_anforanden:  Cleaned anforanden DataFrame

    Returns:
        Dict mapping flag name to DataFrame of flagged rows
    """
    flags: dict[str, pd.DataFrame] = {}

    # Null ID
    flags["null_id_ledamoter"] = flag_null_id(
        df_ledamoter, id_col="intressent_id", source="ledamoter"
    )
    flags["null_id_voteringar"] = flag_null_id(
        df_voteringar, id_col="votering_id", source="voteringar"
    )
    flags["null_id_anforanden"] = flag_null_id(
        df_anforanden, id_col="anforande_id", source="anforanden"
    )

    # Null name
    flags["null_namn_ledamoter"] = flag_null_namn(
        df_ledamoter,
        namn_cols=["tilltalsnamn", "efternamn"],
        source="ledamoter",
    )
    flags["null_namn_voteringar"] = flag_null_namn(
        df_voteringar,
        namn_cols=["fornamn", "efternamn", "namn"],
        source="voteringar",
    )
    flags["null_namn_anforanden"] = flag_null_namn(
        df_anforanden,
        namn_cols=["talare"],
        source="anforanden",
    )

    # Attendance / absence top 10
    flags["narvaro_franvaro_topp10"] = flag_franvaro_topp10(df_voteringar)

    # Drop empty flag tables before passing on
    flags = {k: v for k, v in flags.items() if not v.empty}

    return flags


if __name__ == "__main__":
    from clean import clean

    df_ledamoter = clean(pd.read_csv("../data/ledamoter.csv"))
    df_voteringar = clean(pd.read_csv("../data/voteringar.csv"))
    df_anforanden = clean(pd.read_csv("../data/anforanden.csv"))

    results = run_flags(df_ledamoter, df_voteringar, df_anforanden)

    for flag_name, df_flag in results.items():
        print(f"\n{flag_name}: {len(df_flag)} rows")
        print(df_flag[["flag_reason", "flag_source", "flag_col"]].head(3).to_string(index=False))
