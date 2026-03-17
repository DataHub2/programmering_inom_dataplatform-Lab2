import pandas as pd

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    This is the cleaning step in the transform.
    - Erase whitespace 
    - Make all small letters
    - Change empty strings to Null
    """
    str_cols = df.select_dtypes(include="object").columns

    # White spaces
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Lower case
    df[str_cols] = df[str_cols].apply(lambda col: col.str.lower())

    # Empty strings to Null
    df[str_cols] = df[str_cols].apply(lambda col: col.replace("", pd.NA))

    # Removed: bool_map that converted j/n to True/False in rost and ar_replik
    # caused mixed datatypes (bool + str) in same column, inconsistent for db storage -> som vi diskuterade 

    return df


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
