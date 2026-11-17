import os
import time
import streamlit as st
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, OrGroup, AndGroup
from whoosh import scoring, highlight

INDEX_DIR = "index_dir"

st.set_page_config(
    page_title="Wikinews Italia Search",
    page_icon="📰",
    layout="wide"
)

@st.cache_resource
def load_index():
    if not os.path.exists(INDEX_DIR):
        return None
    return open_dir(INDEX_DIR)

def search_news(ix, query_str, limit=10, use_bm25=True, use_or=False, date_from="", date_to=""):
    start_t = time.perf_counter()
    
    # Scelta funzione di scoring (BM25F vs TF-IDF)
    weighting = scoring.BM25F(B=0.75, K1=1.2) if use_bm25 else scoring.TF_IDF()
    group_mode = OrGroup if use_or else AndGroup

    with ix.searcher(weighting=weighting) as searcher:
        # Ricerca multi-campo su titolo e corpo (rispetta il field_boost=2.0 sul titolo)
        parser = MultifieldParser(["title", "body"], schema=ix.schema, group=group_mode)
        query = parser.parse(query_str)

        # Recupera un pool più ampio se dobbiamo filtrare per data
        fetch_limit = limit * 5 if (date_from or date_to) else limit
        results = searcher.search(query, limit=fetch_limit)
        
        # Configura snippet con evidenziazione in grassetto/colore
        results.fragmenter.charlimit = None
        results.formatter = highlight.HtmlFormatter(tagname="mark")

        formatted_results = []
        for hit in results:
            doc_date = hit.get("date", "N/D")
            if date_from and doc_date != "N/D" and doc_date < date_from:
                continue
            if date_to and doc_date != "N/D" and doc_date > date_to:
                continue

            snippet = hit.highlights("body", top=2)
            if not snippet:
                snippet = hit.get("body", "")[:260] + "..."

            formatted_results.append({
                "title": hit["title"],
                "url": hit["url"],
                "date": doc_date,
                "score": round(hit.score, 2),
                "snippet": snippet
            })
            if len(formatted_results) >= limit:
                break

    elapsed_ms = (time.perf_counter() - start_t) * 1000
    return formatted_results, elapsed_ms

# --- INTERFACCIA UTENTE ---
st.title("📰 Motore di Ricerca — it.wikinews.org")
st.caption("Ingegneria dei dati 2026/2027 • Homework 4 • 12.250 articoli indicizzati")

ix = load_index()
if ix is None:
    st.error("Indice non trovato! Esegui prima `python indexer.py`.")
    st.stop()

# Sidebar con opzioni utili per la demo live
with st.sidebar:
    st.header("⚙️ Parametri di Ricerca")
    model_choice = st.radio(
        "Modello di Ranking",
        ["BM25F (Consigliato)", "TF-IDF (Baseline)"],
        index=0
    )
    operator_choice = st.radio(
        "Operatore tra termini",
        ["AND (Tutti i termini)", "OR (Almeno un termine)"],
        index=0
    )
    num_results = st.slider("Numero massimo risultati", min_value=5, max_value=50, value=10, step=5)
    
    st.divider()
    st.subheader("📅 Filtro Temporale")
    date_from = st.text_input("Da data (AAAA-MM-GG)", placeholder="es. 2020-01-01")
    date_to = st.text_input("A data (AAAA-MM-GG)", placeholder="es. 2025-03-20")

# Barra di ricerca principale
col1, col2 = st.columns([5, 1])
with col1:
    query_input = st.text_input(
        "Inserisci la tua query in italiano:",
        placeholder="Es. elezioni presidente repubblica, olimpiadi invernali, terremoto centro italia..."
    )
with col2:
    st.write("")
    st.write("")
    search_clicked = st.button("🔍 Cerca", use_container_width=True, type="primary")

if query_input:
    use_bm25 = model_choice.startswith("BM25F")
    use_or = operator_choice.startswith("OR")
    
    results, latency_ms = search_news(
        ix,
        query_input,
        limit=num_results,
        use_bm25=use_bm25,
        use_or=use_or,
        date_from=date_from.strip(),
        date_to=date_to.strip()
    )

    st.success(f"Trovati **{len(results)}** risultati mostrati in **{latency_ms:.2f} ms** ({model_choice})")
    st.divider()

    if not results:
        st.info("Nessun articolo trovato. Prova a usare l'operatore OR nella barra laterale o termini più generali.")
    else:
        for i, res in enumerate(results, start=1):
            st.markdown(f"### {i}. [{res['title']}]({res['url']})")
            st.caption(f"📅 Ultima modifica: **{res['date']}**  |  🎯 Score rilevanza: **{res['score']}**")
            st.markdown(res["snippet"], unsafe_allow_html=True)
            st.divider()