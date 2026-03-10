import pandas as pd

def clean_kalender(raw_data):

    kalender_root = raw_data.get("kalenderlista", {})
    handelser = kalender_root.get("kalender", [])

    cleaned = []

    for h in handelser:

        start = h.get("DTSTART")
        slut = h.get("DTEND")

        # konvertera datum
        if start:
            start = pd.to_datetime(start, format="%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M")

        if slut:
            slut = pd.to_datetime(slut, format="%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M")

        cleaned.append({
            "id": h.get("UID"),
            "titel": h.get("SUMMARY"),
            "start": start,
            "slut": slut,
            "plats": h.get("LOCATION"),
            "kategori": h.get("CATEGORIES")
        })

    return cleaned