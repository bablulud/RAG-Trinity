# import os

# # --- LLM and API Configuration ---
# # Use environment variables to keep your secrets safe
# os.environ["OPENAI_API_KEY"] = "<set via environment variable>"
# #

# # --- LLM and API Configuration ---
# LLM_CONFIG_LIST = [
#     {
#         "model": "gpt-4o",
#         "api_key": os.getenv("OPENAI_API_KEY"),
#     },
# ]

# # --- RAG and Vector DB Configuration ---
# # Get the absolute path to the project root directory
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# # The path where your raw PDF documents are stored
# PDF_SOURCE_PATH = os.path.join(PROJECT_ROOT, "pdfs/")

# # The absolute path where ChromaDB will persist its data
# CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db/")

# # The name of the ChromaDB collection to use for your documents
# CHROMA_COLLECTION_NAME = "insurance_docs"

# # The embedding model to use for converting text to vectors
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# # --- Text Splitter Configuration ---
# CHUNK_SIZE = 1000
# CHUNK_OVERLAP = 200

# # --- Agent Configuration ---
# ASSISTANT_SYSTEM_MESSAGE = (
#     "You are an expert assistant for answering questions about insurance policies. "
#     "You will be provided with relevant document snippets to answer the user's questions. "
#     "Always cite the document snippet you are using to formulate your answer."
# )

import os
# === OpenAI API Key ===
# Set this externally (never hardcode):
#   Unix:  export OPENAI_API_KEY="your-key"
#   Windows PowerShell:  $env:OPENAI_API_KEY="your-key"
# Only required for asking questions (the LLM step). Indexing uses a local
# embedding model and needs no API key.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === LLM Configuration ===
LLM_MODEL = "gpt-4o-mini"
LLM_CONFIG_LIST = [
    {
        "model": LLM_MODEL,
        "api_key": OPENAI_API_KEY,
    },
]


# embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# === RAG / Vector DB Configuration ===
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PDF_SOURCE_PATH = os.path.join(PROJECT_ROOT, "pdfs/")
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db/")
CHROMA_COLLECTION_NAME = "documents"

# Number of chunks to retrieve per question (across ALL indexed PDFs).
TOP_K = 8

# === Embedding model ===
# Claude does not provide its own embeddings. Two options:
# 1. Continue using a local embedding model (e.g., sentence-transformers) as before:
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# 2. (Optional) Use a third‑party service like Voyage AI for higher-quality embeddings.
#    If you go that route you’d set up VOYAGE_API_KEY externally and call their API instead. See docs for voyageai. :contentReference[oaicite:3]{index=3}

# === Chunking / Splitting ===
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# === Assistant Prompt ===
ASSISTANT_SYSTEM_MESSAGE = (
    "You are a helpful assistant that answers questions using only the provided "
    "document snippets. Each snippet is labeled with its source file. Base your "
    "answer strictly on these snippets and cite the source file(s) you used. "
    "If the answer is not contained in the snippets, say you don't know."
)
