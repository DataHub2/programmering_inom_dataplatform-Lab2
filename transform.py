import pandas as pd


def transform_data(df):#function for cleaning up raw data
    df = df.copy() #jobba i en kopia
    for col in df.columns: #remove blankspaces and into lowercase for uniformity
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()
            df[col] = df[col].str.lower()


    return df