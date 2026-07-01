
import os
from src.agents.rag_agents import setup_rag_agents
from src.db_management.chroma_db import get_chroma_client, create_collection
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL

def main():
    # You must have your OPENAI_API_KEY set as an environment variable
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY not found. Please set it in your environment.")
        return

    print("--- RAG Agent is ready! ---")
    print("Please make sure you have run 'python scripts/run_indexer.py' at least once.")
    
    # --- Step 1: Initialize ChromaDB and get the collection ---
    print("Connecting to ChromaDB...")
    client = get_chroma_client(db_path=CHROMA_DB_PATH)
    # The get_or_create_collection is used here to ensure the collection exists
    # and to get the collection object to pass to the agents.
    chroma_collection = create_collection(client, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL)
    
    # --- Step 2: Set up the Autogen agents with the collection ---
    rag_proxy_agent, assistant = setup_rag_agents(chroma_collection)
    
    # --- Step 3: Start the conversation ---
    rag_proxy_agent.initiate_chat(
        assistant, 
        message=rag_proxy_agent.message_generator,
        problem="what are the 529 SAVINGS PLANS?"
    )

if __name__ == "__main__":
    main()