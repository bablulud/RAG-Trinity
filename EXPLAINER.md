# RAG-Trinity — Walkthrough

So the project is a small Retrieval-Augmented Generation agent I built for answering questions about insurance policy documents. The idea is simple: you've got a pile of dense insurance PDFs, nobody wants to read them, so instead you ask a plain-English question and the system pulls the relevant passages and writes back an answer that cites where it came from.

## The big picture

The way I like to explain it is that there are really two phases. First there's an offline **indexing** phase where I chew through the PDFs once and load everything into a vector database. Then there's the **query** phase where the agent actually answers questions against that database. They're decoupled on purpose — you only pay the parsing cost once, and after that every question is fast.

The overall path looks like this:

```
PDFs → parse → chunk → embed → ChromaDB → agent retrieves → LLM answers
```

## How indexing works

That first phase lives in `scripts/run_indexer.py`, and you run it once before anything else.

I use **pdfplumber** to open each PDF and walk it page by page. The reason I reached for pdfplumber specifically is that insurance docs are full of tables — coverage limits, premium schedules, that kind of thing — and it can pull tables out as structured rows, not just mash them into garbled text. So I extract both the running text and the tables and stitch them together.

Then there's the chunking step. You can't just dump a whole document into an embedding model, so I split the text into roughly 1000-character chunks with a 200-character overlap. The overlap matters — it keeps a sentence that straddles a chunk boundary from getting cut in half and losing its meaning. I'm using LangChain's `RecursiveCharacterTextSplitter` for that, which tries to break on paragraph and line boundaries first before it falls back to splitting mid-word.

Each chunk then gets embedded and stored in **ChromaDB**. One thing I made a deliberate choice on: the embeddings run locally with `all-MiniLM-L6-v2` from sentence-transformers. No API call, no per-token cost, and it runs fine on a laptop. Everything lands in a persistent Chroma collection called `insurance_docs`, and each chunk carries a bit of metadata pointing back to its source PDF so answers can be traced.

That code is in `src/data_processing/processor.py` (the parsing and chunking) and `src/db_management/chroma_db.py` (the Chroma client and the actual indexing).

## How answering works

The query side is `main.py`, and this is where I leaned on **Autogen** for the agent orchestration.

I set up two agents that talk to each other. The first is a `RetrieveUserProxyAgent` — its job is retrieval. When a question comes in, it embeds the question, searches the Chroma collection for the closest-matching chunks, and pulls those out as context. The second is an `AssistantAgent`, which is the one actually backed by the LLM. It takes the retrieved snippets plus the question and writes the final answer. I gave it a system prompt that tells it to always cite the snippet it used, because for something like insurance you really don't want the model freelancing — you want it grounded in the actual policy text.

The wiring for both of those is in `src/agents/rag_agents.py`. Right now `main.py` kicks off the conversation with a hardcoded sample question just to demonstrate the loop end to end.

## Where everything lives

| File | What it does |
|------|--------------|
| `config.py` | central config — API keys, paths, chunk sizes, model names, the system prompt |
| `src/data_processing/processor.py` | turns a PDF into clean text chunks |
| `src/db_management/chroma_db.py` | the ChromaDB client and indexing logic |
| `src/agents/rag_agents.py` | the two Autogen agents |
| `main.py` | entry point for asking a question |
| `Dockerfile` | packages it up on a slim Python 3.10 image |

## Running it

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
# drop your PDFs into pdfs/
python scripts/run_indexer.py      # build the vector DB, run once
python main.py                     # ask a question
```

## One honest caveat

If you read the config you'll notice some leftover comments mentioning Claude and Anthropic. That's a bit of a red herring — the code actually runs against OpenAI's `gpt-4o-mini` through Autogen. I was clearly experimenting with swapping the model provider at some point and never cleaned up the comments. The retrieval and chunking layers are model-agnostic anyway, so pointing it at a different LLM is mostly a config change, not a rewrite — which is honestly one of the things I like about how it's structured.
