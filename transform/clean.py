import pandas as pd

def clean(df: pd.DataFrame, critical_cols: list[str] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    This is the cleaning step in the transform.
    - Erase whitespace 
    - Make all small letters
    - Change empty strings to Null
    - Normalize j/n values -> voteringar
    - Separera rader med null i kritiska kolumner
    """
    str_cols = df.select_dtypes(include=["object", "str"]).columns

    # White spaces
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Lower case
    df[str_cols] = df[str_cols].apply(lambda col: col.str.lower())

    # Empty strings to Null
    df[str_cols] = df[str_cols].apply(lambda col: col.replace("", pd.NA))

    # Normalize j/n values in voteringar
    bool_map = {"j": True, "n": False, "ja": True, "nej": False}
    for col in ["ar_replik", "rost"]:
        if col in df.columns:
            df[col] = df[col].map(lambda x: bool_map.get(x, x) if pd.notna(x) else x)

    # Separates rejected rows --> Christoffers önskan!
    if critical_cols:
        existing_cols = [c for c in critical_cols if c in df.columns]
        rejected_mask = df[existing_cols].isna().any(axis=1)
        df_rejected = df[rejected_mask].copy()
        df_clean = df[~rejected_mask].copy()
    else:
        df_clean = df.copy()
        df_rejected = pd.DataFrame()

    return df_clean, df_rejected


if __name__ == "__main__":
    files = {
        "data/ledamoter.csv":  ["intressent_id", "efternamn", "tilltalsnamn"],
        "data/kalender.csv":   [],
        "data/dokument.csv":   [],
        "data/voteringar.csv": ["votering_id", "namn"],
        "data/anforanden.csv": ["anforande_id", "talare"],
    }
    for path, critical_cols in files.items():
        df = pd.read_csv(path)
        df_clean, df_rejected = clean(df, critical_cols=critical_cols)
        print(f"{path}: clean={df_clean.shape}, rejected={df_rejected.shape}")