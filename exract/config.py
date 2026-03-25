APIS = [
    {
        "url": "https://data.riksdagen.se/kalender/?org=kamm&utformat=json",
        "csv": "data/kalender.csv",
        "record_path": ["kalenderlista", "kalender"],
        "kafka_topic": "riksdag.kalender",
    },
    {
        "url": "https://data.riksdagen.se/personlista/?utformat=json",
        "csv": "data/ledamoter.csv",
        "record_path": ["personlista", "person"],
        "kafka_topic": "riksdag.ledamoter",
    },
    {
        "url": "https://data.riksdagen.se/dokumentlista/?sz=500&utformat=json",
        "csv": "data/dokument.csv",
        "record_path": ["dokumentlista", "dokument"],
        "kafka_topic": "riksdag.dokument",
    },
    {
        "url": "https://data.riksdagen.se/voteringlista/?sz=500&utformat=json",
        "csv": "data/voteringar.csv",
        "record_path": ["voteringlista", "votering"],
        "kafka_topic": "riksdag.voteringar",
    },
    {
        "url": "https://data.riksdagen.se/anforandelista/?sz=500&utformat=json",
        "csv": "data/anforanden.csv",
        "record_path": ["anforandelista", "anforande"],
        "kafka_topic": "riksdag.anforanden",
    },
]