\# Motore di Ricerca — it.wikinews.org (Homework 4)



Sistema di Information Retrieval full-text con interfaccia Web realizzato per il corso di \*\*Ingegneria dei dati 2026/2027\*\* (Prof. Paolo Merialdo). Il sistema indicizza le notizie in lingua italiana dal dump ufficiale Wikimedia Enterprise HTML (`itwikinews-NS0-20250320-ENTERPRISE-HTML.json.tar.gz`).



\## Architettura del Progetto



\- `indexer.py`: Parsing in streaming del dump `.tar.gz`, pulizia del DOM HTML tramite `BeautifulSoup` (`lxml`), analisi linguistica in italiano (`LanguageAnalyzer("it")` con rimozione stopwords e stemming Snowball) e creazione dell'indice invertito Whoosh multi-campo (`title` con boost `2.0x`, `body`, `url`, `date`).

\- `app.py`: Interfaccia Web sviluppata in \*\*Streamlit\*\* che permette la ricerca multi-campo con scoring \*\*BM25F\*\* (o confronto con baseline \*\*TF-IDF\*\*), operatori booleani (`AND`/`OR`), filtri per intervallo temporale ed evidenziazione contestuale degli snippet.

\- `evaluate.py`: Suite di benchmark su 30 query eterogenee per misurare tempi di indicizzazione, occupazione su disco, latenza (media, P50, P95) e confronto qualitativo (`Title Precision@5`) tra configurazione finale e baseline.



\## Installazione e Utilizzo



\### 1. Clona il repository e crea il virtual environment

```bash

git clone https://github.com/lorenzolacopo22/wikinews-search-hw4

cd wikinews-search

python -m venv venv

