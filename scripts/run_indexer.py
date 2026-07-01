# /Users/vishalj/Downloads/rag_project/scripts/run_indexer.py
import sys
import os

# Add the project's root directory to the Python path
# This assumes the script is one level deep (e.g., scripts/run_indexer.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processing.processor import process_single_pdf
from src.db_management.chroma_db import get_chroma_client, create_collection, index_chunks
from config import (
    PDF_SOURCE_PATH, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, 
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
)

def main():
    # --- Step 1: Initialize ChromaDB Client ---
    client = get_chroma_client(db_path = CHROMA_DB_PATH)
    collection = create_collection(client, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL)

    # --- Step 2: Process all PDFs and index them ---
    if not os.path.exists(PDF_SOURCE_PATH):
        print(f"Error: PDF source path '{PDF_SOURCE_PATH}' not found. Please add your PDFs.")
        return

    pdf_files = [f for f in os.listdir(PDF_SOURCE_PATH) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in '{PDF_SOURCE_PATH}'.")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_SOURCE_PATH, pdf_file)
        chunks, _ = process_single_pdf(pdf_path, CHUNK_SIZE, CHUNK_OVERLAP)
        if chunks:
            index_chunks(collection, chunks, pdf_path)
    
    print("\n--- Indexing complete. The vector database is ready! ---")

if __name__ == "__main__":
    main()