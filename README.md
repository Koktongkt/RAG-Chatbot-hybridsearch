## 🧠 Local RAG Pipeline Overview

This project implements a fully local **Retrieval-Augmented Generation (RAG)** pipeline using:

---

### 📥 1. Document Ingestion Pipeline

A flexible ingestion pipeline to process original documents (PDF, Word, TXT, etc.).

**Pipeline logic:**

- **Primary Engine**: MarkItDown  
- **Fallback Engine**: PyPDFReader (used if MarkItDown fails)  
- **Backup Engine**: OCR processing  
- **Validation Logic**:
  ```python
  len(text) > 20

🗄️ 2. Vector Storage & Indexing

ChromaDB is used as the main vector database to store embeddings.

Default embedding model: MXBAI (1024 dimensions)
Can be swapped for smaller or larger models depending on requirements
🔍 BM25 (Sparse Retrieval)
Applied as part of a hybrid search strategy
Runs in parallel during document ingestion
Workflow:
Documents are chunked
Chunks are embedded and stored in ChromaDB
Chunks are also tokenized and indexed using BM25

⚠️ Note:
BM25 index is stored in-memory, so it must be reinitialized on every application startup.

🔎 3. Hybrid Search Strategy

Uses a weighted scoring mechanism to combine dense and sparse retrieval:

Final Score = α × Dense Score + (1 - α) × Sparse Score

α (alpha) is configurable depending on the use case
Allows tuning between:
Semantic similarity (ChromaDB)
Keyword matching (BM25)
🔄 Reranking
A secondary reranker model is used to refine the final Top-K results
Top-K is configurable in config.py

4. Orchestration (LangChain)
LangChain is used for orchestrating:
- Local LLM (via Ollama)
- RAG pipeline flow
Prompt templates are used for:
- Prompt tuning
- Standardized output formatting

