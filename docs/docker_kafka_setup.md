# Guide för installation av Docker & Kafka

Detta dokument förklarar hur man sätter upp och kör den lokala Kafka-infrastrukturen med hjälp av Docker. Det beskriver syftet med konfigurationsfilen och tillhandahåller de nödvändiga kommandona för att hantera miljön.

## 1. Förkunskaper: Att få Docker att fungera

Innan några kommandon körs i terminalen måste Docker-motorn vara aktiv på din maskin.

* **Krav:** Öppna applikationen **Docker Desktop**.
* **Verifiering:** Vänta tills Docker-ikonen i din systemmeny indikerar att motorn är igång. Om motorn är offline kommer terminalen att returnera felet "Cannot connect to the Docker daemon".

## 2. Vad filen docker-compose.yml gör

Filen `docker-compose.yml` fungerar som en ritning för vår infrastruktur. När den exekveras läser Docker denna fil och utför följande åtgärder:

* **Nedladdning av avbildning:** Den hämtar den officiella Kafka-mjukvaran (`confluentinc/cp-kafka:latest`) från nätet.
* **Isolering:** Den skapar ett privat, isolerat nätverk på din dator specifikt för detta projekt.
* **Containerisering:** Den startar en container med namnet `riksdagen_logg_server` som kör Kafka-servern.
* **Portmappning:** Den öppnar en brygga mellan port `9092` inuti containern och port `9092` på din fysiska dator. Detta tillåter externa applikationer (som vår Python-datapipeline) att skicka data in i det isolerade Kafka-systemet via `localhost:9092`.
* **Notering om versionsvarning:** Filen innehåller `version: '3.8'`. Moderna Docker Compose V2-miljöer kommer att skriva ut en varning om att detta attribut är föråldrat. Denna varning är ytlig, har absolut ingen teknisk påverkan på funktionaliteten och kan ignoreras helt.

## 3. Grundläggande Docker-kommandon

Exekvera dessa kommandon i terminalen. Du måste befinna dig i den exakta katalogen där filen `docker-compose.yml` ligger (katalogen `schema`).

* **Starta infrastrukturen:**
  `docker-compose up -d`
  Laddar ner nödvändiga filer, bygger nätverket och startar containern i bakgrunden (`-d` står för detached mode).

* **Kontrollera aktiva containrar:**
  `docker ps`
  Listar alla Docker-containrar som körs för tillfället. Du bör se `riksdagen_logg_server` listad med statusen "Up".

* **Visa interna systemloggar:**
  `docker logs riksdagen_logg_server`
  Skriver ut Kafka-serverns interna loggar. Detta är oumbärligt för felsökning om Python-applikationen misslyckas med att ansluta.

* **Stäng ner infrastrukturen:**
  `docker-compose down`
  Stänger säkert ner den aktiva containern och raderar det isolerade nätverket. Det raderar inte den nedladdade mjukvaruavbildningen, vilket innebär att nästa uppstart går betydligt snabbare.
