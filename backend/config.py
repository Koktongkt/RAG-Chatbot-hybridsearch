import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = Path(__file__).parent
DOCUMENTS_DIR = PROJECT_ROOT / "Documents"
DB_DIR = BACKEND_ROOT / "data"
CHROMA_DB_PATH = DB_DIR / "chroma_db"

# Create necessary directories
DB_DIR.mkdir(exist_ok=True)
CHROMA_DB_PATH.mkdir(exist_ok=True)

# LLM Configuration
LLM_MODEL = "gemma4:26b"  
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "your_ollama_server_url")  # Set your Ollama server URL in .env

# Embeddings Configuration
EMBEDDING_MODEL = "mxbai-embed-large"  # Ollama embedding model
EMBEDDING_BACKEND = "ollama"  # 'huggingface' or 'ollama'
# Note: Dimension is 384 for all-MiniLM-L6-v2, smaller dimension means faster but less accurate retrieval. Adjust based on your needs.

# RAG Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K_RESULTS = 15  # Number of chunks to retrieve for context

# Flask Configuration
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
