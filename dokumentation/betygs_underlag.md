# Riksdagsprojekt
### Projektdokumentation – Data Platform Lab 2

---

## 1. Syfte & Mål

Projektet syftar till att bygga en webbaserad dashboard som visar information om Sveriges riksdag – möten, ledamöter, beslut och omröstningar. Dashboarden ska ge en snabb överblick och möjlighet att analysera data visuellt.

### Projektmål
- Följa riksdagens aktuella möten och beslut i realtid
- Visa statistik per ledamot och parti
- Bygga en lättanvänd dashboard med filtrering och grafer
- Integrera en modern data platform med Kafka, FastAPI och Supabase

---

## 2. Planering & Roller

| Roll | Ansvar |
|------|--------|
| Dokumentation | Zineb – dokumentation och projektbeskrivning |
| Backend & Databas | Gruppmedlem – Supabase-databas, API-integration |
| Frontend & Dashboard | Gruppmedlem – Streamlit, dashboard-design |
| Test & Funktionalitet | Gruppmedlem – testdata och kvalitetssäkring |

---

## 3. Systemarkitektur & Dataflöde

Projektet bygger på en modern data platform-arkitektur där data flödar från Riksdagens öppna API genom ett pipeline-system och slutligen visas i en interaktiv dashboard.

### Dataflöde
1. **Riksdagens API** → FastAPI hämtar data (ledamöter, voteringar, anföranden)
2. **FastAPI** → Kafka producer publicerar data som meddelanden på Kafka-topics
3. **Kafka consumer** → konsumerar meddelanden och lagrar dem i Supabase
4. **Supabase** → Streamlit hämtar data via Supabase Python-client
5. **Streamlit** → visar dashboarden för användaren

### Tech Stack

| Teknologi | Användning |
|-----------|------------|
| FastAPI | REST API – hämtar data från Riksdagens API |
| Apache Kafka | Meddelandeköer – skickar riksdagsdata till Supabase |
| Supabase | Databas & backend – lagrar och serverar data |
| Streamlit | Frontend – interaktiv dashboard |
| Docker / Docker Compose | Containerisering av alla tjänster |
| Python, Pandas, Plotly | Databehandling och visualisering |

---

## 4. Projektstruktur

| Mapp / Fil | Beskrivning |
|------------|-------------|
| `main/` | Huvudlogik – FastAPI-applikation och Kafka-producer |
| `transform/` | Datatransformering – bearbetar rådata från API:et |
| `pages/` | Streamlit-sidor – varje fil är en sida i dashboarden |
| `dashboard/` | Dashboard-konfiguration och övergripande layout |
| `utils/` | Hjälpfunktioner – återanvändbara kodmoduler |
| `config/` | Konfigurationsfiler – miljövariabler och inställningar |
| `streamlit/` | Streamlit-specifika inställningar och entry point |
| `docker-compose.yml` | Definierar och startar alla containers |

---

## 5. Databas – Supabase

Supabase används som backend-databas. Data lagras i följande tabeller:

| Tabell | Beskrivning | Viktiga kolumner |
|--------|-------------|-----------------|
| `members` | Riksdagsledamöter | id, namn, parti, valdistrikt, bild_url |
| `parties` | Partiinformation | id, namn, förkortning, färg, antal_ledamöter |
| `meetings` | Riksdagsmöten | id, datum, tid, ämne, status |
| `votes` | Omröstningar | id, ledamot_id, beslut, röst, datum |

---

## 6. Dashboard – Streamlit

### Sidor i dashboarden

Varje `.py`-fil i mappen `pages/` blir automatiskt en sida i Streamlit:

| Fil | Sida | Innehåll |
|-----|------|----------|
| `first_page.py` | Startsida / Översikt | KPI-kort: antal ledamöter, möten, beslut |
| `pages_anfonaden.py` | Anföranden | Tal och debatter från riksdagen |
| `pages_voteringar.py` | Voteringar | Omröstningsresultat per parti och ledamot |

### Dashboard-funktioner
- **KPI-kort** – antal ledamöter, möten, aktiva ärenden
- **Tabeller** – möten, ledamöter, ärenden med sortering
- **Grafer** – omröstningar per parti, beslut över tid (Plotly)
- **Filtrering & Sökning** – per datum, ledamot, parti

---

## 7. Installation – Docker & FastAPI-miljö

### Förkunskaper

Innan några kommandon körs i terminalen måste Docker-motorn vara aktiv på din maskin.

- **Krav:** Öppna applikationen **Docker Desktop**
- **Verifiering:** Vänta tills Docker-ikonen i din systemmeny indikerar att motorn är igång. Om motorn är offline visas felet: `Cannot connect to the Docker daemon`

### Vad filerna gör

#### docker-compose.yml
Filen fungerar som en ritning för hela infrastrukturen och startar tre tjänster:

| Tjänst | Beskrivning |
|--------|-------------|
| `fastapi` | Bygger och kör FastAPI-applikationen på port `8000` |
| `db` | Startar en PostgreSQL-databas (`postgres:15`) med namnet `postgres_db` |
| `kafka` | Startar en Kafka-server (`confluentinc/cp-kafka:7.6.0`) på port `9092` |

Alla tjänster körs i ett gemensamt isolerat nätverk (`app_network`) och kommunicerar internt.

> **Notering om versionsvarning:** Filen innehåller `version: '3.8'`. Moderna Docker Compose V2-miljöer skriver ut en varning om att detta attribut är föråldrat. Varningen har ingen teknisk påverkan och kan ignoreras.

#### Dockerfile
Beskriver hur FastAPI-containern byggs:
1. Utgår från `python:3.11-slim`
2. Installerar systemberoenden (`gcc`, `libpq-dev`, `librdkafka-dev` m.fl.)
3. Installerar Python-paket via `uv`
4. Startar applikationen med `uvicorn`

#### Viktigt: Volymmontering
Endast datakatalogen monteras in i containern:
```yaml
volumes:
  - ./data:/app/data
```
> Montera **inte** hela `/app`-katalogen – det skulle skriva över den virtuella Python-miljön (`.venv`) som byggs inuti containern.

---

## 8. Docker-kommandon

Exekvera kommandona i terminalen från katalogen där `docker-compose.yml` ligger.

| Kommando | Beskrivning |
|----------|-------------|
| `docker compose up -d --build` | Bygg images och starta alla containers i bakgrunden |
| `docker compose up -d` | Starta befintliga containers utan att bygga om |
| `docker compose down` | Stäng ner alla containers |
| `docker compose restart streamlit` | Snabb omstart av Streamlit utan rebuild |
| `docker compose logs -f streamlit` | Följ Streamlit-loggarna live |
| `docker compose exec streamlit bash` | Gå in i Streamlit-containern |
| `docker ps` | Lista alla körande containers |

### Stäng ner och starta från scratch
```bash
docker compose down
docker compose up -d --build
```
Nödvändigt vid större konfigurationsändringar, t.ex. ändringar i volymmontering.

### Kontrollera aktiva containers
```bash
docker ps
```
Du bör se `fastapi_app`, `postgres_db` och `riksdagen_logg_server` med statusen **"Up"** eller **"Healthy"**.

### Visa loggar per tjänst
```bash
docker compose logs fastapi
docker compose logs db
docker compose logs kafka
```

### Öppna dashboarden
```
http://localhost:8501
```

---

## 9. Beroenden & Installation

```bash
pip install streamlit supabase pandas plotly
```

---

## 10. Test & Kvalitetssäkring

- Kontrollera att data från Supabase visas korrekt i tabeller och grafer
- Verifiera att filtrering per datum, ledamot och parti fungerar
- Testa att Kafka-meddelanden når Supabase utan dataförlust
- Säkerställ att dashboarden är responsiv och användarvänlig
- Kör `git pull` och verifiera att alla teammedlemmars ändringar fungerar tillsammans

---

## 11. Git & Pull Request-guide

### Huvudregel
> **Vi jobbar ALDRIG direkt på `main`.**

### Superviktig regel
Ändringar syns först i PR när de är:
1. **staged** – `git add ...`
2. **committed** – `git commit ...`
3. **pushed** – `git push`

Om du hoppar över ett steg händer ingenting (och det är normalt).

---

### Steg 0 – Kolla läget (innan du gör något)
```bash
git status
git branch
```
Målet: du ska se att du är på rätt branch och att din working tree är clean.

---

### Steg 1 – Uppdatera `main`
```bash
git checkout main
git pull origin main
```
Du vill ALLTID utgå från senaste versionen.

---

### Steg 2 – Skapa ny branch
```bash
git checkout -b <typ>/<kort-beskrivning>
```
**Exempel:**
- `docs/update-readme`
- `feat/clean-ads-keywords`
- `fix/null-title-bug`

---

### Steg 3 – Gör din ändring

Ändra filer, skapa nya filer osv. Kolla vad du faktiskt har gjort:
```bash
git status
git diff
```

---

### Steg 4 – Stage (lägg till det du menar)

**A) Befintlig fil (rekommenderat):**
```bash
git add -p
```
Undviker att råka lägga med skräp (data, secrets, random filer).

**B) Ny fil (untracked):**
```bash
git add path/to/new_file
```
Exempel:
```bash
git add docs/my_new_doc.md
git status
```

---

### Steg 5 – Commit
```bash
git commit -m "docs(scope): short description"
```
**Exempel:**
- `docs(readme): clarify setup steps`
- `feat(clean): add keyword tagging`
- `fix(parser): handle empty description`

---

### Steg 6 – Pusha din branch
```bash
git push -u origin <branch-namn>
```
Exempel:
```bash
git push -u origin docs/update-readme
```

---

### Steg 7 – Skapa Pull Request (PR) på GitHub

1. Gå till GitHub → repo → **Pull requests** → **New pull request**
2. Base: `main`, Compare: din branch
3. Fyll i PR-mallen/checklistan: `pull_requests_checklist.md`
4. Request review (se `team_workflow_and_rules.md`)

---

### Steg 8 – Merge (vi använder SQUASH)

När PR är godkänd:
- Välj **Squash and merge**
- Radera branchen (**Delete branch**)

> **Varför Squash?** Flera commits i branchen blir 1 commit på main → ren historik.

---

### Steg 9 – Synka lokalt och städa

```bash
git checkout main
git pull origin main
```

Radera din lokala branch:
```bash
git branch -d <branch-namn>
```

Städa remote-spår (valfritt men cleant):
```bash
git fetch --prune
```

---

### Vanliga problem och snabbfixar

**`No changes` när jag kör `git add -p`**
Du har troligen bara nya (untracked) filer.
```bash
git status
git add path/to/file
```

**`Everything up-to-date` men jag ser inte min ändring på GitHub**
Du har troligen inte committat än, eller står på fel branch, eller pushade innan commit.
```bash
git status
git branch
git log --oneline -n 5
```

**`rejected (fetch first)` vid push**
Remote har commits du saknar.
```bash
git pull --rebase origin main
# Försök sen pusha igen
```

**Jag råkade ändra på `main`**
Skapa en branch direkt och fortsätt där:
```bash
git checkout -b fix/move-work-off-main
```

---

## 12. Sammanfattning

Projektet demonstrerar en komplett data platform-pipeline från öppen API-data till interaktiv visualisering. Genom att kombinera FastAPI, Kafka, Supabase, Streamlit och Docker har gruppen byggt en skalbar och modern arkitektur för att analysera och presentera riksdagsdata i realtid.