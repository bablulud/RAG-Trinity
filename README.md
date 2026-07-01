# RAG-Trinity — Insurance Policy RAG Agent

Small Python RAG app. Ask questions about insurance PDFs, get cited answers. Uses **Autogen** agents + **ChromaDB** vector store.

## Flow

```
PDFs → parse → chunk → embed → ChromaDB → agent retrieves → LLM answers
```

## Architecture — how each RAG concept maps to the code

```mermaid
---
title: "RAG-Trinity — how each RAG concept maps to the code"
---
flowchart LR
    subgraph INDEX["INDEXING · offline, run once — scripts/run_indexer.py"]
        direction LR
        D["Documents<br/><i>pdfs/*.pdf</i>"]
        L["Load / Parse<br/><i>parse_pdf · pdfplumber</i><br/>processor.py"]
        C["Chunk<br/><i>chunk_text · 1000 / 200</i><br/>processor.py"]
        E1["Embed<br/><i>all-MiniLM-L6-v2</i><br/>chroma_db.py"]
        D --> L --> C --> E1
    end

    VDB[("Vector Store<br/><b>ChromaDB</b><br/>collection: documents")]

    subgraph QUERY["QUERY · online, per question — main.py"]
        direction LR
        Q["Question<br/><i>interactive / one-shot</i>"]
        E2["Embed query<br/><i>all-MiniLM-L6-v2</i>"]
        R["Retrieve top-K<br/><i>collection.query</i><br/>main.py"]
        A["Augment<br/><i>build_context → prompt</i><br/>main.py"]
        G["Generate<br/><i>OpenAI gpt-4o-mini</i><br/>main.py"]
        ANS["Answer + citations"]
        Q --> E2 --> R --> A --> G --> ANS
    end

    E1 -->|upsert vectors| VDB
    E2 -.->|same embedding space| VDB
    VDB -->|top-K chunks| R

    classDef index fill:#d6f5d6,stroke:#2e7d32,color:#1b3d1b;
    classDef query fill:#ffe6c7,stroke:#e08a00,color:#5a3d00;
    classDef store fill:#e7d6ff,stroke:#7b3fe4,color:#2e1a4a;
    class D,L,C,E1 index;
    class Q,E2,R,A,G,ANS query;
    class VDB store;
```

> Green = offline indexing (retrieve step is built here), purple = the shared vector store, orange = online query (retrieve → augment → generate). Each box names the RAG concept and the code that implements it.

**0. (Optional) Grab web pages as PDFs** (`scripts/url_to_pdf.py`):

- Single page: `python scripts/url_to_pdf.py https://example.com`
- Whole site (follows all same-domain links): `python scripts/url_to_pdf.py https://example.com --crawl`
- Saves one PDF per page into `pdfs/` (uses headless Chromium via Playwright).

**1. Index ALL PDFs** (`scripts/run_indexer.py`) — run after adding/updating PDFs:

- Loops over **every** `*.pdf` in `pdfs/`.
- `process_single_pdf` (`src/data_processing/processor.py`) — pdfplumber pulls text + tables per page, then `chunk_text` cuts into 1000-char chunks, 200 overlap.
- `index_chunks` (`src/db_management/chroma_db.py`) — embeds chunks with `all-MiniLM-L6-v2` (sentence-transformers, local) and **upserts** into the persistent ChromaDB collection `documents` (idempotent, so re-running just adds new files).

**2. Ask across all PDFs** (`main.py`):

- Opens the same ChromaDB collection (every indexed PDF).
- Retrieves the top-`TOP_K` most relevant chunks **from across all documents**.
- Sends them to the LLM (`gpt-4o-mini`) which answers and cites the source file(s).
- Interactive loop, or one-shot: `python main.py "your question"`.

## Pieces

| File | Job |
|------|-----|
| `config.py` | key, paths, chunk sizes, model, prompt, `TOP_K` |
| `scripts/url_to_pdf.py` | URL/site → PDF into `pdfs/` |
| `scripts/run_indexer.py` | index every PDF in `pdfs/` |
| `src/data_processing/processor.py` | PDF → text → chunks |
| `src/db_management/chroma_db.py` | vector DB client + upsert index |
| `main.py` | ask questions across all PDFs |
| `src/agents/rag_agents.py` | legacy AutoGen agents (no longer used by `main.py`) |
| `Dockerfile` | python:3.10-slim container |

## Config knobs (`config.py`)

- `EMBEDDING_MODEL = "all-MiniLM-L6-v2"` — local sentence-transformers embeddings.
- `CHUNK_SIZE = 1000`, `CHUNK_OVERLAP = 200`.
- `CHROMA_COLLECTION_NAME = "documents"`.
- `TOP_K = 8` — chunks retrieved per question.
- `LLM_MODEL = "gpt-4o-mini"` — OpenAI chat model.

## Run

```bash
pip install -r requirements.txt
playwright install chromium          # only if you use scripts/url_to_pdf.py

# (optional) pull a site into pdfs/
python scripts/url_to_pdf.py https://example.com --crawl

# index needs NO API key (local embeddings)
python scripts/run_indexer.py        # build/refresh vector DB from ALL pdfs

# asking needs your key
export OPENAI_API_KEY="your-key"     # do NOT hardcode
python main.py                       # interactive Q&A across all PDFs
python main.py "what does the site say about leasing?"
```
