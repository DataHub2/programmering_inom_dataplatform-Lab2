## Riksdagens Data Plattform 

Länk till dashboard: https://programmeringinomdataplatform-lab2-huky8ttdgiyhtvykvg6unv.streamlit.app/

### Denna plattform är byggd för att automatisera insamling, bearbetning och lagring av data från Sveriges Riksdag. Systemet fokuserar på skalbarhet och händelsestyrd arkitektur (Event-Driven Architecture).


### Systemarkitektur
* Plattformen är byggd med en mikrotjänst-arkitektur som körs helt i Docker.

### FastAPI (Ingestion Layer):

* Fungerar som systemets motor. Den använder en asynkron scheduler (APScheduler) för att hämta data från externa API:er var 24:e timme.

### Apache Kafka (Streaming Layer): 

* Hanterar loggar och dataflöden mellan tjänster, vilket möjliggör asynkron bearbetning.

### PostgreSQL (Storage Layer): 
* Lagrar den bearbetade datan för långtidslagring.

### Kafka-UI: 

* Används för att övervaka dataströmmarna i realtid.


## Teknisk Implementering

### Data Ingestion (main.py)

Vi använder en lifespan-manager i FastAPI för att hantera systemets livscykel:

* Automatisering: Vid uppstart initieras en AsyncIOScheduler.

* Schemaläggning: Varje API i konfigurationen (APIS) schemaläggs för hämtning en gång per dygn för att hålla plattformen uppdaterad.

* Cold Start: Systemet utför en initial hämtning (fetch_posts) direkt vid start för att säkerställa att data finns tillgänglig omedelbart. 

### Docker Stack

Systemet orkestreras via docker-compose, vilket säkerställer:

* Service Dependency: FastAPI väntar på att både databasen och Kafka är "Healthy" innan den startar.

* Persistence: Data sparas i Docker-volymer för att undvika dataförlust vid omstart.

### Installation & Start

* Skapa en .env-fil med nödvändiga miljövariabler (se .env.example).

* Kör följande kommando:

docker-compose up --build

* Backend nås på localhost:8000 och Kafka-UI på localhost:8080.



--------------------------------------------------------------
# Designbeslut och Arkitektur

### Från API till Plattform (Data Ingestion & Automation)

* Genom att använda AsyncIOScheduler i FastAPI har man automatiserat dataflödet. Systemet agerar som en vaktpost som hämtar färsk data från externa API:er (Riksdagen) var 24:e timme. Detta säkerställer att plattformen alltid är uppdaterad utan manuell handpåläggning.


### Kafka som "Krockkudde" (Event Streaming & Resiliens)

* Vi använder Apache Kafka som ett streaming-lager mellan datakällan och lagringen. Kafka fungerar som en buffert (en krockkudde). Om vår Postgres-databas skulle ligga nere för underhåll, förlorar vi ingen data; meddelandena ligger säkert kvar i Kafka tills databasen är redo att ta emot dem igen.


### Docker-orkestrering (Infrastruktur som Kod)

* Med Docker Compose har jag definierat hela plattformens infrastruktur. Jag använder healthchecks för att skapa en intelligent startordning; FastAPI-appen startar först när den bekräftat att både databasen och Kafka är 'Healthy'. Detta eliminerar anslutningsfel vid uppstart.

--------------------------------------------------------------




