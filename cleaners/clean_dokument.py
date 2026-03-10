def clean_dokument(data):

    cleaned = []

    docs = data.get("dokumentlista", {}).get("dokument", [])

    if isinstance(docs, dict):
        docs = [docs]

    for d in docs:

        if not isinstance(d, dict):
            continue

        cleaned.append({
            "id": d.get("id"),
            "titel": d.get("titel"),
            "typ": d.get("typ"),
            "datum": d.get("datum"),
            "organ": d.get("organ"),
            "parti": d.get("parti"),
            "dok_url": d.get("dok_url")
        })

    return cleaned