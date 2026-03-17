import pandas as pd

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    This is the cleaning step in the transform.
    - Erase whitespace 
    - Make all small letters
    - Change empty strings to Null
    - Normalize j/n values -> voteringar
    """
    str_cols = df.select_dtypes(include="object").columns

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

    return df

# startar clean.
if __name__ == "__main__":
    files = [
        "data/ledamoter.csv",
        "data/kalender.csv",
        "data/dokument.csv",
        "data/voteringar.csv",
        "data/anforanden.csv",
    ]
    for path in files:
        df = pd.read_csv(path)
        df_clean = clean(df)
        print(f"{path}: {df_clean.shape}")