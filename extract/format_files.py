import pandas as pd


def format_files(
    df: pd.DataFrame,
    keep: list = None,                     #lista med kolumner att behålla
    rename: dict = None,                   #dict med gamla till nya kolumnnamn
) -> pd.DataFrame:
    if keep:
        df = df[[c for c in keep if c in df.columns]]  # behåll bara valda kolumner, hoppar över saknade

    if rename:
        df = df.rename(columns=rename)                  # döp om kolumner enligt rename-dict

    return df