def clean_ledamoter(data):

    cleaned = []

    personer = data.get("personlista", {}).get("person", [])

    for person in personer:
        cleaned.append({
            "id": person.get("intressent_id"),
            "namn": person.get("tilltalsnamn"),
            "efternamn": person.get("efternamn"),
            "parti": person.get("parti"),
            "valkrets": person.get("valkrets")
        })

    return cleaned