import os
import json
import time
import tarfile
from bs4 import BeautifulSoup
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import LanguageAnalyzer

# Configurazione percorsi
DUMP_PATH = os.path.join("data", "itwikinews.tar.gz")
INDEX_DIR = "index_dir"

def get_italian_schema():
    # Analyzer completo per l'italiano (lowercase + stopwords italiane + stemming Snowball)
    italian_analyzer = LanguageAnalyzer("it")
    
    return Schema(
        doc_id=ID(stored=True, unique=True),
        title=TEXT(stored=True, analyzer=italian_analyzer, field_boost=2.0),
        body=TEXT(stored=True, analyzer=italian_analyzer),
        url=ID(stored=True),
        date=ID(stored=True)
    )

def clean_html(html_content):
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "lxml")
    for tag in soup(["script", "style", "table"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def build_index():
    if not os.path.exists(DUMP_PATH):
        print(f"ERRORE: File {DUMP_PATH} non trovato! Controlla di averlo scaricato nella cartella data.")
        return

    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)

    print("Creazione schema e inizializzazione indice Whoosh...")
    schema = get_italian_schema()
    ix = create_in(INDEX_DIR, schema)
    writer = ix.writer(limitmb=256)

    start_time = time.time()
    count = 0
    skipped = 0

    print(f"Apertura e lettura in streaming di {DUMP_PATH}...")
    with tarfile.open(DUMP_PATH, "r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            f = tar.extractfile(member)
            if f is None:
                continue

            for line in f:
                try:
                    article = json.loads(line.decode("utf-8"))
                    
                    title = article.get("name", "").strip()
                    url = article.get("url", "")
                    date_mod = article.get("date_modified", "")
                    
                    body_html = article.get("article_body", {}).get("html", "")
                    clean_text = clean_html(body_html)

                    if not title or len(clean_text) < 50:
                        skipped += 1
                        continue

                    writer.add_document(
                        doc_id=str(article.get("identifier", count)),
                        title=title,
                        body=clean_text,
                        url=url,
                        date=date_mod[:10] if date_mod else "N/D"
                    )
                    count += 1

                    if count % 1000 == 0:
                        print(f"Indicizzati {count} articoli... ({time.time() - start_time:.1f}s)")

                except Exception as e:
                    skipped += 1
                    continue

    print("Salvataggio e ottimizzazione indice su disco (commit)...")
    writer.commit()
    elapsed = time.time() - start_time
    print(f"\nCOMPLETATO!")
    print(f"- Articoli indicizzati: {count}")
    print(f"- Articoli scartati: {skipped}")
    print(f"- Tempo totale: {elapsed:.2f} secondi")

if __name__ == "__main__":
    build_index()