# NAIS Research Work - Kibana vs Grafana

Projekat prikazuje isti dataset web access logova kroz Elasticsearch, Kibana i Grafana. Cilj je da se podaci pripreme iz CSV fajlova, učitaju u Elasticsearch indeks i zatim analiziraju kroz dva različita alata za vizualizaciju.

## Šta je urađeno

Podaci se nalaze u `input/` folderu. Osnovni dataset `access_logs.csv` se spaja sa `servers.csv`, čime nastaje `access_logs_merged.csv`. Spojeni fajl sadrži HTTP logove i podatke o serverima: vreme zahteva, metodu, putanju, status kod, vreme odziva, količinu poslatih podataka, user agent, IP adresu, referrer, ime servera, region i rolu.

Dodate su skripte za:

- spajanje CSV fajlova u `input/access_logs_merged.csv`
- generisanje osnovnog Markdown izveštaja `input/basic_info_dataset.md`
- učitavanje podataka u Elasticsearch indeks `web-logs`

Docker Compose podiže tri servisa:

- `elasticsearch` kao centralnu bazu za logove
- `kibana` za istraživanje i analizu podataka iz Elasticsearch-a
- `grafana` za dashboard prikaz preko automatski podešenog Elasticsearch datasource-a

## Kako je povezano

`docker-compose.yml` definiše Elasticsearch, Kibanu i Grafanu u istoj Docker mreži. Zbog toga se servisi međusobno ne gađaju preko `localhost`, već preko imena servisa.

Kibana je povezana direktno kroz environment vrednost:

```yaml
ELASTICSEARCH_HOSTS: http://elasticsearch:9200
```

To znači da Kibana zna gde je Elasticsearch, ali Data View za indeks `web-logs` se pravi ručno u Kibana interfejsu.

Grafana je povezana preko fajla `grafana-datasource.yml`. Taj fajl se mountuje u Grafana kontejner:

```yaml
./grafana-datasource.yml:/etc/grafana/provisioning/datasources/elasticsearch.yml:ro
```

Grafana pri startovanju automatski pročita taj fajl i doda Elasticsearch datasource za indeks iz promenljive `ELASTICSEARCH_INDEX`.

## Zašto je ovako odrađeno

Elasticsearch je centralno mesto za čuvanje logova jer dobro radi sa vremenskim podacima, status kodovima, IP adresama i agregacijama. Kibana je prirodan alat za Elasticsearch i dobar je za brzo istraživanje podataka, filtriranje i pravljenje Data View-a.

Grafana je dodata da bi se isti podaci mogli prikazati kroz dashboard-e i uporediti sa Kibana pristupom. Automatski datasource za Grafanu smanjuje ručno podešavanje: čim se Grafana pokrene, Elasticsearch izvor podataka je već spreman.

Skripta `load_data_db/load_data.py` koristi eksplicitno mapiranje indeksa kako bi Kibana i Grafana pravilno prepoznale tipove polja. Na primer, `timestamp` je `date`, `ip_address` je `ip`, status i response time su numerička polja, a kategorije poput `method`, `region`, `role` i `status_class` su `keyword`.

CSV kolona `name` se u Elasticsearch-u čuva kao `server_name`, da bude jasnije da vrednost predstavlja ime servera.

## Struktura projekta

```text
.
├── docker-compose.yml
├── grafana-datasource.yml
├── requirements.txt
├── input/
│   ├── access_logs.csv
│   ├── servers.csv
│   ├── access_logs_merged.csv
│   ├── one_csv.py
│   ├── dataset_info.py
│   └── basic_info_dataset.md
└── load_data_db/
    └── load_data.py
```

## Podešavanje `.env`

Fajl `.env` se ne šalje na Git jer može sadržati lokalne portove i lozinke. Za lokalno pokretanje koristi vrednosti poput ovih:

```env
ELASTIC_VERSION=8.19.15
GRAFANA_VERSION=13.0.2

ELASTICSEARCH_CONTAINER_NAME=elasticsearch
KIBANA_CONTAINER_NAME=kibana
GRAFANA_CONTAINER_NAME=grafana

ELASTICSEARCH_PORT=9200
KIBANA_PORT=5601
GRAFANA_PORT=3000

ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=web-logs
ACCESS_LOGS_CSV=input/access_logs_merged.csv

KIBANA_URL=http://localhost:5601
GRAFANA_URL=http://localhost:3000

ES_JAVA_OPTS=-Xms1g -Xmx1g

KIBANA_SECURITY_KEY=local-dev-kibana-security-key-32chars
KIBANA_ENCRYPTION_KEY=local-dev-kibana-encryption-key-32chars
KIBANA_REPORTING_KEY=local-dev-kibana-reporting-key-32chars

LOAD_DATA_CHUNK_SIZE=1000
LOAD_DATA_MAX_ERRORS=5

GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

## Pokretanje

Prvo instaliraj Python dependency-je:

```powershell
pip install -r requirements.txt
```

Ako treba ponovo spojiti ulazne CSV fajlove, pokreni:

```powershell
cd input
python .\one_csv.py
python .\dataset_info.py
cd ..
```

Zatim podigni Elasticsearch, Kibanu i Grafanu:

```powershell
docker compose up -d
```

Proveri da je Compose konfiguracija validna:

```powershell
docker compose config
```

Učitaj podatke u Elasticsearch:

```powershell
python .\load_data_db\load_data.py --recreate-index
```

Flag `--recreate-index` briše postojeći indeks `web-logs` i pravi ga ponovo. Za kasnije pokretanje bez brisanja indeksa može se koristiti:

```powershell
python .\load_data_db\load_data.py
```

Skripta koristi stabilan `_id` za svaki red, pa ponovljeni import istog CSV fajla ne pravi duplikate.

## Pristup alatima

Elasticsearch je dostupan na:

```text
http://localhost:9200
```

Kibana je dostupna na:

```text
http://localhost:5601
```

U Kibani ručno kreiraj Data View:

```text
Name: web-logs
Index pattern: web-logs
Timestamp field: timestamp
```

Grafana je dostupna na:

```text
http://localhost:3000
```

Podrazumevani login iz lokalnog `.env` fajla je:

```text
Username: admin
Password: admin
```

Grafana automatski dobija Elasticsearch datasource iz `grafana-datasource.yml`, tako da nije potrebno ručno dodavanje datasource-a.

## Korisne komande

Provera statusa kontejnera:

```powershell
docker compose ps
```

Pregled logova:

```powershell
docker compose logs -f elasticsearch
docker compose logs -f kibana
docker compose logs -f grafana
```

Gašenje servisa bez brisanja podataka:

```powershell
docker compose down
```

Gašenje servisa uz brisanje Docker volume podataka:

```powershell
docker compose down -v
```

## Napomene

Ovo podešavanje je namenjeno lokalnom development i istraživačkom radu. Elasticsearch sigurnost je isključena kroz `xpack.security.enabled=false`, što nije preporučeno za produkciju.

Ako se promeni naziv indeksa u `.env`, potrebno je da ista vrednost ostane usklađena kroz:

- `ELASTICSEARCH_INDEX`
- `load_data_db/load_data.py`
- `grafana-datasource.yml`
- Kibana Data View

