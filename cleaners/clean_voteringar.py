def clean_voteringar(data):

    cleaned = []

    voteringar = data.get("voteringlista", {}).get("votering", [])

    for v in voteringar:
        cleaned.append({
            "id": v.get("votering_id"),
            "titel": v.get("punkt"),
            "datum": v.get("datum"),
            "resultat": v.get("resultat")
        })

    return cleaned