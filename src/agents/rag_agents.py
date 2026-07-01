import autogen
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen import AssistantAgent
from chromadb.api.models.Collection import Collection
from config import (
    LLM_CONFIG_LIST,
    ASSISTANT_SYSTEM_MESSAGE,
    EMBEDDING_MODEL
)

def setup_rag_agents(chroma_collection: Collection):
    """
    Sets up and returns the Autogen agents, passing the live ChromaDB collection.
    """
    # Initialize the LLM configuration
    llm_config = {
        "config_list": LLM_CONFIG_LIST,
        "temperature": 0
    }

    # The agent that orchestrates the RAG process
    # It will use the provided ChromaDB collection directly
    rag_proxy_agent = RetrieveUserProxyAgent(
        name="RAG_Assistant",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        retrieve_config={
            "task": "qa",
            # "docs_path": "pdfs/sample.pdf",  # Leave empty to prevent re-indexing
            "embedding_model": EMBEDDING_MODEL,
            "client": None,  # No client needed, as we'll pass the collection directly
            "collection_name": chroma_collection.name,
            "vector_db_type": "chromadb",
            "collection": chroma_collection, # Pass the live collection object
        },
        code_execution_config=False,
    )

    # An assistant agent to generate the final answer
    assistant = AssistantAgent(
        name="Assistant",
        system_message=ASSISTANT_SYSTEM_MESSAGE,
        llm_config=llm_config
    )
    
    return rag_proxy_agent, assistant