# Guide för installation av Docker & FastAPI-miljö

Detta dokument förklarar hur man sätter upp och kör den lokala infrastrukturen med hjälp av Docker. Det beskriver syftet med konfigurationsfilerna och tillhandahåller de nödvändiga kommandona för att hantera miljön.

## 1. Förkunskaper: Att få Docker att fungera

Innan några kommandon körs i terminalen måste Docker-motorn vara aktiv på din maskin.

* **Krav:** Öppna applikationen **Docker Desktop**.
* **Verifiering:** Vänta tills Docker-ikonen i din systemmeny indikerar att motorn är igång. Om motorn är offline kommer terminalen att returnera felet "Cannot connect to the Docker daemon".

## 2. Vad filerna gör

### docker-compose.yml
Filen fungerar som en ritning för hela infrastrukturen och startar tre tjänster:

* **fastapi** – Bygger och kör FastAPI-applikationen på port `8000`.
* **db** – Startar en PostgreSQL-databas (`postgres:15`) med namnet `postgres_db`.
* **kafka** – Startar en Kafka-server (`confluentinc/cp-kafka:7.6.0`) med namnet `riksdagen_logg_server` på port `9092`.

Alla tjänster körs i ett gemensamt isolerat nätverk (`app_network`) och kommunicerar med varandra internt.

**Notering om versionsvarning:** Filen innehåller `version: '3.8'`. Moderna Docker Compose V2-miljöer skriver ut en varning om att detta attribut är föråldrat. Varningen har ingen teknisk påverkan och kan ignoreras.

### Dockerfile
Beskriver hur FastAPI-containern byggs:
1. Utgår från `python:3.11-slim`
2. Installerar systemberoenden (gcc, libpq-dev, librdkafka-dev m.fl.)
3. Installerar Python-paket via `uv`
4. Startar applikationen med `uvicorn`

### Viktigt: Volymmontering
Endast datakatalogen monteras in i containern:
```yaml
volumes:
  - ./data:/app/data
```
Det är viktigt att **inte** montera hela `/app`-katalogen, eftersom det skulle skriva över den virtuella Python-miljön (`.venv`) som byggs inuti containern.

## 3. Grundläggande Docker-kommandon

Exekvera dessa kommandon i terminalen från katalogen där `docker-compose.yml` ligger.

* **Bygg och starta infrastrukturen:**
  `docker compose up -d --build`
  Bygger images, skapar nätverket och startar alla containrar i bakgrunden. Använd `--build` när du har gjort ändringar i Dockerfile eller applikationskoden.

* **Starta utan att bygga om:**
  `docker compose up -d`
  Startar befintliga containrar utan att bygga om images.

* **Stäng ner och starta om från scratch:**
  `docker compose down`
  följt av
  `docker compose up -d --build`
  Nödvändigt vid större konfigurationsändringar, t.ex. ändringar i volymmontering.

* **Kontrollera aktiva containrar:**
  `docker ps`
  Listar alla körande containrar. Du bör se `fastapi_app`, `postgres_db` och `riksdagen_logg_server` med statusen "Up" eller "Healthy".

* **Visa loggar för en tjänst:**
  `docker compose logs fastapi`
  `docker compose logs db`
  `docker compose logs kafka`
  Skriver ut respektive containers loggar. Oumbärligt för felsökning om en tjänst inte startar korrekt.