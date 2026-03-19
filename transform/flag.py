import pandas as pd

# Runs after the cleaning step. Takes cleaned DataFrames as input and returns
# a dict of flag tables to be passed on to the reject handler.

STANDARD_PARTIER = {"S", "SD", "M", "C", "V", "KD", "MP", "L", "-"}


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

    # One summary row per member — not all voting rows
    franvaro_rows = (
        df_voteringar[
            df_voteringar["intressent_id"].isin(topp10_franvaro_ids)
            & (df_voteringar["rost"] == "frånvarande")
        ]
        .groupby("intressent_id", as_index=False)
        .first()
    )
    franvaro_rows["flag_reason"] = "topp10_franvaro"

    narvaro_rows = (
        df_voteringar[df_voteringar["intressent_id"].isin(topp10_narvaro_ids)]
        .groupby("intressent_id", as_index=False)
        .first()
    )
    narvaro_rows["flag_reason"] = "topp10_narvaro"

    flagged = pd.concat([franvaro_rows, narvaro_rows], ignore_index=True)
    flagged["flag_source"] = "voteringar"
    flagged["flag_col"] = "rost"
    return flagged


def flag_talare_ej_i_ledamoter(
    df_anforanden: pd.DataFrame, df_ledamoter: pd.DataFrame
) -> pd.DataFrame:
    """
    Flags speeches where the speaker's intressent_id does not exist in ledamoter.
    Could indicate ministers, speakers of the house, or extraction errors.

    Args:
        df_anforanden:  Cleaned anforanden DataFrame
        df_ledamoter:   Cleaned ledamoter DataFrame

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    # Normalize IDs to string for safe comparison across int/float dtypes
    led_ids = set(df_ledamoter["intressent_id"].astype(str).str.split(".").str[0])
    anf_ids = df_anforanden["intressent_id"].astype(str).str.split(".").str[0]

    mask = ~anf_ids.isin(led_ids)
    flagged = df_anforanden[mask].copy()
    flagged["flag_reason"] = "talare_ej_i_ledamoter"
    flagged["flag_source"] = "anforanden"
    flagged["flag_col"] = "intressent_id"
    return flagged


def flag_ogiltigt_parti(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Flags rows where the parti column contains a non-standard value,
    e.g. 'TALMANNEN', 'FÖRSTE VICE TALMANNEN' — roles rather than party codes.

    Args:
        df:      Cleaned DataFrame containing a 'parti' column
        source:  Source name for traceability

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    if "parti" not in df.columns:
        return pd.DataFrame()

    mask = ~df["parti"].str.upper().isin({p.upper() for p in STANDARD_PARTIER})
    flagged = df[mask].copy()
    flagged["flag_reason"] = "ogiltigt_parti"
    flagged["flag_source"] = source
    flagged["flag_col"] = "parti"
    return flagged


def flag_okant_parti(df_voteringar: pd.DataFrame) -> pd.DataFrame:
    """
    Flags members in voteringar with party code '-', which cannot be linked
    to the parties table via foreign key without special handling.

    Args:
        df_voteringar:  Cleaned voteringar DataFrame

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    mask = df_voteringar["parti"] == "-"
    flagged = (
        df_voteringar[mask]
        .groupby("intressent_id", as_index=False)
        .first()
    )
    flagged["flag_reason"] = "okant_parti"
    flagged["flag_source"] = "voteringar"
    flagged["flag_col"] = "parti"
    return flagged


def flag_hog_franvaro_andel(df_voteringar: pd.DataFrame) -> pd.DataFrame:
    """
    Flags members whose absence rate exceeds one standard deviation above the mean.

    Args:
        df_voteringar:  Cleaned voteringar DataFrame

    Returns:
        DataFrame of flagged rows — one row per flagged member
    """
    franvaro = (
        df_voteringar[df_voteringar["rost"] == "frånvarande"]
        .groupby("intressent_id")
        .size()
        .reset_index(name="antal_franvaro")
    )
    totalt = (
        df_voteringar
        .groupby("intressent_id")
        .size()
        .reset_index(name="totalt")
    )
    merged = totalt.merge(franvaro, on="intressent_id", how="left")
    merged["antal_franvaro"] = merged["antal_franvaro"].fillna(0)
    merged["franvaro_andel"] = merged["antal_franvaro"] / merged["totalt"]

    mean = merged["franvaro_andel"].mean()
    std = merged["franvaro_andel"].std()
    grans = mean + std

    hog_franvaro_ids = merged[merged["franvaro_andel"] > grans]["intressent_id"].tolist()

    flagged = (
        df_voteringar[df_voteringar["intressent_id"].isin(hog_franvaro_ids)]
        .groupby("intressent_id", as_index=False)
        .first()
    )
    flagged["flag_reason"] = "hog_franvaro_andel"
    flagged["flag_source"] = "voteringar"
    flagged["flag_col"] = "rost"
    return flagged


def flag_tom_anforandetext(df_anforanden: pd.DataFrame) -> pd.DataFrame:
    """
    Flags speeches where body text is null — likely an extraction issue.

    Args:
        df_anforanden:  Cleaned anforanden DataFrame

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    mask = df_anforanden["anforandetext"].isna()
    flagged = df_anforanden[mask].copy()
    flagged["flag_reason"] = "tom_anforandetext"
    flagged["flag_source"] = "anforanden"
    flagged["flag_col"] = "anforandetext"
    return flagged


def flag_tom_kolumn(
    df: pd.DataFrame, kolumn: str, source: str, flag_reason: str
) -> pd.DataFrame:
    """
    Flags all rows when an entire column is null — used for iort and organ
    which are almost entirely empty in the source data.

    Args:
        df:           Cleaned DataFrame
        kolumn:       Column name to check
        source:       Source name for traceability
        flag_reason:  Flag reason string

    Returns:
        DataFrame of flagged rows, or empty DataFrame if column has any values
    """
    if kolumn not in df.columns:
        return pd.DataFrame()

    # Only flag if the entire column is null — not partial nulls
    if df[kolumn].isna().all():
        flagged = df.copy()
        flagged["flag_reason"] = flag_reason
        flagged["flag_source"] = source
        flagged["flag_col"] = kolumn
        return flagged

    return pd.DataFrame()


def flag_foddar_outlier(df_ledamoter: pd.DataFrame) -> pd.DataFrame:
    """
    Flags members whose birth year is more than 2 standard deviations
    from the mean — potential data entry errors worth verifying.

    Args:
        df_ledamoter:  Cleaned ledamoter DataFrame

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    mean = df_ledamoter["fodd_ar"].mean()
    std = df_ledamoter["fodd_ar"].std()

    mask = (
        (df_ledamoter["fodd_ar"] < mean - 2 * std) |
        (df_ledamoter["fodd_ar"] > mean + 2 * std)
    )
    flagged = df_ledamoter[mask].copy()
    flagged["flag_reason"] = "foddar_outlier"
    flagged["flag_source"] = "ledamoter"
    flagged["flag_col"] = "fodd_ar"
    return flagged


def flag_skev_konsfordelning(df_ledamoter: pd.DataFrame) -> pd.DataFrame:
    """
    Flags parties where gender distribution deviates significantly from
    the riksdag average — one gender exceeds 75% of the party's members.

    Args:
        df_ledamoter:  Cleaned ledamoter DataFrame

    Returns:
        DataFrame of flagged rows — all members of skewed parties
    """
    kon_parti = df_ledamoter.groupby(["parti", "kon"]).size().unstack(fill_value=0)
    kon_parti["totalt"] = kon_parti.sum(axis=1)

    skeva_partier = []
    for kon_col in ["man", "kvinna"]:
        if kon_col in kon_parti.columns:
            andel = kon_parti[kon_col] / kon_parti["totalt"]
            skeva = andel[andel > 0.75].index.tolist()
            skeva_partier.extend(skeva)

    skeva_partier = list(set(skeva_partier))

    flagged = df_ledamoter[df_ledamoter["parti"].isin(skeva_partier)].copy()
    flagged["flag_reason"] = "skev_konsfordelning"
    flagged["flag_source"] = "ledamoter"
    flagged["flag_col"] = "kon"
    return flagged


def flag_felaktigt_id_format(
    df_anforanden: pd.DataFrame, df_ledamoter: pd.DataFrame
) -> pd.DataFrame:
    """
    Flags speeches where intressent_id is stored as float (e.g. 4.102316e+11)
    instead of integer string, which causes join failures against ledamoter.

    Args:
        df_anforanden:  Cleaned anforanden DataFrame
        df_ledamoter:   Cleaned ledamoter DataFrame

    Returns:
        DataFrame of flagged rows with added metadata columns
    """
    # Check if intressent_id in anforanden is float dtype
    if df_anforanden["intressent_id"].dtype != object:
        # Float format — any non-null value is potentially misformatted
        mask = df_anforanden["intressent_id"].notna()
        flagged = df_anforanden[mask].copy()
        flagged["flag_reason"] = "felaktigt_id_format"
        flagged["flag_source"] = "anforanden"
        flagged["flag_col"] = "intressent_id"
        return flagged

    return pd.DataFrame()


def run_flags(
    df_ledamoter: pd.DataFrame,
    df_voteringar: pd.DataFrame,
    df_anforanden: pd.DataFrame,
    df_kalender: pd.DataFrame,
    df_dokument: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """
    Runs all flag checks and returns a dict of flag tables.
    Add new flag calls here as the pipeline grows.

    Args:
        df_ledamoter:   Cleaned ledamoter DataFrame
        df_voteringar:  Cleaned voteringar DataFrame
        df_anforanden:  Cleaned anforanden DataFrame
        df_kalender:    Cleaned kalender DataFrame
        df_dokument:    Cleaned dokument DataFrame

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
    flags["null_id_kalender"] = flag_null_id(
        df_kalender, id_col="UID", source="kalender"
    )
    flags["null_id_dokument"] = flag_null_id(
        df_dokument, id_col="id", source="dokument"
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

    # Speakers not found in ledamoter
    flags["talare_ej_i_ledamoter"] = flag_talare_ej_i_ledamoter(
        df_anforanden, df_ledamoter
    )

    # Non-standard party values in anforanden
    flags["ogiltigt_parti_anforanden"] = flag_ogiltigt_parti(
        df_anforanden, source="anforanden"
    )

    # Members with unknown party in voteringar
    flags["okant_parti_voteringar"] = flag_okant_parti(df_voteringar)

    # High absence rate — more than 1 std above mean
    flags["hog_franvaro_andel"] = flag_hog_franvaro_andel(df_voteringar)

    # Empty body text in speeches
    flags["tom_anforandetext"] = flag_tom_anforandetext(df_anforanden)

    # Entirely empty columns
    flags["tom_iort"] = flag_tom_kolumn(
        df_ledamoter, kolumn="iort", source="ledamoter", flag_reason="tom_iort"
    )
    flags["tom_organ"] = flag_tom_kolumn(
        df_dokument, kolumn="organ", source="dokument", flag_reason="tom_organ"
    )

    # Birth year outliers
    flags["foddar_outlier"] = flag_foddar_outlier(df_ledamoter)

    # Skewed gender distribution per party
    flags["skev_konsfordelning"] = flag_skev_konsfordelning(df_ledamoter)

    # Float format on intressent_id in anforanden
    flags["felaktigt_id_format"] = flag_felaktigt_id_format(
        df_anforanden, df_ledamoter
    )

    # Drop empty flag tables before passing on
    flags = {k: v for k, v in flags.items() if not v.empty}

    return flags


if __name__ == "__main__":
    from clean import clean

    df_ledamoter  = clean(pd.read_csv("../data/ledamoter.csv"))
    df_voteringar = clean(pd.read_csv("../data/voteringar.csv"))
    df_anforanden = clean(pd.read_csv("../data/anforanden.csv"))
    df_kalender   = clean(pd.read_csv("../data/kalender.csv"))
    df_dokument   = clean(pd.read_csv("../data/dokument.csv"))

    results = run_flags(df_ledamoter, df_voteringar, df_anforanden, df_kalender, df_dokument)

    # Sample columns to show per flag — shows the most relevant columns for each source
    preview_cols = {
        "ledamoter":  ["tilltalsnamn", "efternamn", "parti", "flag_reason", "flag_col"],
        "voteringar": ["namn", "parti", "rost", "flag_reason", "flag_col"],
        "anforanden": ["talare", "parti", "flag_reason", "flag_col"],
        "dokument":   ["titel", "doktyp", "flag_reason", "flag_col"],
        "kalender":   ["summary", "dtstart", "flag_reason", "flag_col"],
    }

    for flag_name, df_flag in results.items():
        source = df_flag["flag_source"].iloc[0]
        cols = [c for c in preview_cols.get(source, []) if c in df_flag.columns]
        cols = cols + ["flag_reason", "flag_col"] if cols else ["flag_reason", "flag_source", "flag_col"]
        cols = list(dict.fromkeys(cols))  # remove duplicates while preserving order

        print(f"\n{'='*60}")
        print(f"Flagg: {flag_name}")
        print(f"Källa: {source} | Antal flaggade rader: {len(df_flag)}")
        print(df_flag[cols].head(3).to_string(index=False))