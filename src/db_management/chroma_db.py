import chromadb
from chromadb.utils import embedding_functions
from typing import List

def get_chroma_client(db_path: str) -> chromadb.Client:
    """Returns a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=db_path)

def create_collection(client: chromadb.Client, collection_name: str, embedding_model: str):
    """
    Creates or gets a ChromaDB collection with a specific embedding function.
    """
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model
    )
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_func
    )
    print(f"ChromaDB collection '{collection_name}' ready with {collection.count()} items.")
    return collection

def index_chunks(collection: chromadb.Collection, chunks: List[str], pdf_path: str):
    """Adds a list of text chunks to the ChromaDB collection."""
    if not chunks:
        return
        
    ids = [f"{pdf_path}_{i}" for i in range(len(chunks))]
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=[{"source": pdf_path} for _ in chunks]
    )
    print(f"Indexed {len(chunks)} chunks from {pdf_path}.")