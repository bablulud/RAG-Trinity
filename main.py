"""Ask questions across ALL indexed PDFs.

First index your PDFs (put them in pdfs/, then run once):
    python scripts/run_indexer.py

Then ask questions:
    python main.py                       # interactive loop
    python main.py "what railcars do they offer?"   # one-shot
"""
import os
import sys

from openai import OpenAI

from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_MODEL,
    ASSISTANT_SYSTEM_MESSAGE,
    TOP_K,
)
from src.db_management.chroma_db import get_chroma_client, create_collection


def build_context(results) -> tuple[str, list[str]]:
    """Turn Chroma query results into a labeled context block + source list."""
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    blocks = []
    sources = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        source = os.path.basename((meta or {}).get("source", "unknown"))
        if source not in sources:
            sources.append(source)
        blocks.append(f"[{i}] (source: {source})\n{doc}")
    return "\n\n".join(blocks), sources


def answer_question(llm: OpenAI, collection, question: str) -> None:
    results = collection.query(query_texts=[question], n_results=TOP_K)
    context, sources = build_context(results)

    if not context.strip():
        print("No relevant content found. Have you run scripts/run_indexer.py?")
        return

    response = llm.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": ASSISTANT_SYSTEM_MESSAGE},
            {
                "role": "user",
                "content": f"Document snippets:\n\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    print("\n" + response.choices[0].message.content.strip())
    if sources:
        print("\nSources: " + ", ".join(sources))


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: set OPENAI_API_KEY in your environment to ask questions.")
        return

    client = get_chroma_client(db_path=CHROMA_DB_PATH)
    collection = create_collection(client, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL)

    if collection.count() == 0:
        print("The vector DB is empty. Add PDFs to pdfs/ and run: python scripts/run_indexer.py")
        return

    llm = OpenAI(api_key=api_key)

    one_shot = " ".join(sys.argv[1:]).strip()
    if one_shot:
        answer_question(llm, collection, one_shot)
        return

    print(f"Ask questions across {collection.count()} indexed chunks. Type 'exit' to quit.")
    while True:
        try:
            question = input("\nQuestion> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue
        answer_question(llm, collection, question)


if __name__ == "__main__":
    main()
