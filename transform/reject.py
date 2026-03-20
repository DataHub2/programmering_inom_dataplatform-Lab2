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
        "iort",                  # null
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
        "underrubrik",        # 100% null
    ])

def reject_kalender(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[
        "TRANSP",          # tekniskt iCal-fält, alltid TRANSPARENT
        "XRDREST",         # intern REST-url
        "XRDSOURCEID",     # internt system-ID
        "XRDDOKID",        # internt dok-ID
        "XRDDOKRELID",     # internt relationsID
        "XRDDTSTARTSTATUS",# internt statusfält
        "XRDSOURCE",       # intern källkod (t.ex. "Safir")
        "XRDSORT",         # intern sorteringstid
        "COMMENT",         # 100% null
    ])

def reject_dokument(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[
        "systemdatum",                    # internt
        "rdrest",                         # intern REST-url
        "rddata",                         # intern data-url
        "relurl",                         # relativ url (redundant med url)
        "score",                          # sökrankning, inte analytiskt relevant
        "tempbeteckning",                 # temporär beteckning
        "sokdata.soktyp",                 # intern sökkategori
        "sokdata.statusrad",              # intern statusrad
        "sokdata.brodsmula",              # navigation breadcrumb
        "sokdata.parti_website_url",      # url
        "sokdata.parti_website_namn",     # url-text
        "sokdata.parti_epost",            # kontaktinfo
        "sokdata.parti_telefon",          # kontaktinfo
        "sokdata.parti_telefontider",     # kontaktinfo
        "sokdata.parti_logotyp_img_id",   # bild-ID
        "sokdata.parti_logotyp_img_url",  # bild-url
        "sokdata.parti_logotyp_img_alt",  # bild-alt
        "sokdata.kalenderprio",           # intern prioritet
        "egenskaper.egenskap",            # intern metadata-blob
        "avdelningar.avdelning",          # redundant med avdelning
        "traff",                          # sökträffar — samma som score
        "domain",                         # alltid "rdwebb"
        "database",                       # alltid "kalender"
        #alla 100% null nedanför
        "plats",
        "klockslag",
        "inlamnad",
        "motionstid",
        "tilldelat",
        "url",
        "organ",
        "relaterat_id",
        "beteckning",
        "nummer",
        "dokintressent",
        "filbilaga",
        "struktur",
        "audio",
        "video",
        "debattgrupp",
        "debattdag",
        "beslutsdag",
        "beredningsdag",
        "justeringsdag",
        "beslutad",
        "debattsekunder",
        "ardometyp",
        "reservationer",
        "debatt",
        "sokdata.parti_kod",
        "sokdata.parti_namn",
        "sokdata.parti_mandat",
    ])

def transform(
    df_ledamoter: pd.DataFrame,
    df_voteringar: pd.DataFrame,
    df_anforanden: pd.DataFrame,
    df_kalender: pd.DataFrame,
    df_dokument: pd.DataFrame,
) -> dict[str, pd.DataFrame]:

    # Hämta alla flaggor från flag.py
    flags = run_flags(df_ledamoter, df_voteringar, df_anforanden, df_kalender, df_dokument)

    #flags.pop("narvaro_franvaro_topp10", None)

    # Varje dataset med sitt ID-kolumnnamn
    datasets = {
        "ledamoter":  (df_ledamoter,  "intressent_id"),
        "voteringar": (df_voteringar, "intressent_id"),
        "anforanden": (df_anforanden, "anforande_id"),
        "kalender": (df_kalender, "UID"),
        "dokument": (df_dokument, "id"),
    }

    result = {}

    for name, (df, id_col) in datasets.items():

        relevant_flags = {
            k: v for k, v in flags.items()
            if v["flag_source"].eq(name).any()
        }

        df = add_flags(df, relevant_flags, id_col)

        # Rejekta rader med null ID
        df = df[df[id_col].notna() & (df[id_col].astype(str).str.strip() != "")]

        # Rejekta rader med felaktigt ID-format (endast anforanden)
        if name == "anforanden":
            df = df[df["intressent_id"].apply(
                lambda x: pd.isna(x) or "e+" not in str(x).lower()
            )]

        # Rejekta kolumner per dataset
        if name == "ledamoter":
            df = reject_ledamoter(df)
        elif name == "voteringar":
            df = reject_voteringar(df)
        elif name == "anforanden":
            df = reject_anforanden(df)
        elif name == "kalender":
            df = reject_kalender(df)
        elif name == "dokument":
            df = reject_dokument(df)

        result[name] = df

    return result


if __name__ == "__main__":
    # Läs och städa alla datasets
    df_ledamoter  = clean(pd.read_csv("data/ledamoter.csv"))
    df_voteringar = clean(pd.read_csv("data/voteringar.csv"))
    df_anforanden = clean(pd.read_csv("data/anforanden.csv"))
    df_kalender = clean(pd.read_csv("data/kalender.csv"))
    df_dokument = clean(pd.read_csv("data/dokument.csv"))

    # Kör transform
    result = transform(df_ledamoter, df_voteringar, df_anforanden, df_kalender, df_dokument)

    # Skriv ut summering
    for name, df in result.items():
        flagged_count = (df["flag_reason"] != "").sum()
        print(f"{name}: {len(df)} rader, {flagged_count} flaggade")
        print(f"  kolumner: {df.columns.tolist()}")
        print()
