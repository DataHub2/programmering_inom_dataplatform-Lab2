def clean_anforanden(data):

    cleaned = []

    speeches = data.get("anforandelista", {}).get("anforande", [])

    if isinstance(speeches, dict):
        speeches = [speeches]

    for a in speeches:

        if not isinstance(a, dict):
            continue

        cleaned.append({
            "id": a.get("anforande_id"),
            "talare": a.get("talare"),
            "parti": a.get("parti"),
            "datum": a.get("datum"),
            "text": a.get("anforandetext")
        })

    return cleaned