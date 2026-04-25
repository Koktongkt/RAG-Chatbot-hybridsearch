import logging
from typing import List, Dict, Tuple
import chromadb
from langchain_ollama import OllamaLLM
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
from config import (
    EMBEDDING_MODEL, EMBEDDING_BACKEND, LLM_MODEL, OLLAMA_BASE_URL,
    CHROMA_DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS
)

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        """Initialize RAG engine with ChromaDB and Ollama."""
        try:
            # Initialize embeddings based on backend
            if EMBEDDING_BACKEND == "huggingface":
                logger.info(f"Using HuggingFace embeddings: {EMBEDDING_MODEL}")
                self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            else:  # ollama
                logger.info(f"Using Ollama embeddings: {EMBEDDING_MODEL}")
                self.embeddings = OllamaEmbeddings(
                    model=EMBEDDING_MODEL,
                    base_url=OLLAMA_BASE_URL
                )
            
            # Initialize ChromaDB client with persistent storage
            self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
            
            # Get or create collection - ChromaDB will auto-detect embedding dimensions
            try:
                self.collection = self.chroma_client.get_or_create_collection(
                    name="rag_documents",
                    metadata={"hnsw:space": "cosine"}
                )
            except ValueError as e:
                # If collection exists with wrong dimensions, delete and recreate
                if "dimension" in str(e).lower():
                    logger.warning(f"Collection has mismatched dimensions, recreating: {e}")
                    self.chroma_client.delete_collection(name="rag_documents")
                    self.collection = self.chroma_client.get_or_create_collection(
                        name="rag_documents",
                        metadata={"hnsw:space": "cosine"}
                    )
                else:
                    raise
            
            # Initialize LLM
            self.llm = OllamaLLM(
                model=LLM_MODEL,
                base_url=OLLAMA_BASE_URL
            )
            
            # Initialize text splitter
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Initialize reranker
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            
            # Initialize BM25 - will be built from existing documents
            self.bm25_corpus = []
            self.bm25_corpus_ids = []
            self.bm25_index = None
            self._rebuild_bm25_index()
            
            logger.info("RAG Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            raise

    def ingest_documents(self, documents: List[dict]) -> Dict[str, int]:
        """Ingest documents into ChromaDB and update BM25 index in parallel.
        
        Returns:
            Dict containing:
            - chunk_count: Total number of chunks ingested
            - replaced_count: Number of existing documents that were replaced
            - new_count: Number of new documents added
        """
        try:
            chunk_count = 0
            replaced_count = 0
            new_count = 0
            
            ids = []
            docs = []
            metadatas = []
            embeddings = []
            
            # For BM25 index
            new_tokenized_docs = []
            new_doc_ids = []
            
            # Track which filenames are being processed
            processed_filenames = set()
            
            for doc in documents:
                filename = doc["filename"]
                processed_filenames.add(filename)
                
                # Check if documents with this filename already exist
                existing_ids = self.collection.get(where={"filename": filename})["ids"]
                
                if existing_ids:
                    # Delete existing chunks for this filename
                    self.collection.delete(ids=existing_ids)
                    
                    # Remove from BM25 corpus
                    indices_to_remove = []
                    for i, doc_id in enumerate(self.bm25_corpus_ids):
                        if doc_id.startswith(f"{filename}_chunk_"):
                            indices_to_remove.append(i)
                    
                    # Remove in reverse order to maintain indices
                    for i in sorted(indices_to_remove, reverse=True):
                        del self.bm25_corpus[i]
                        del self.bm25_corpus_ids[i]
                    
                    replaced_count += 1
                    logger.info(f"Replaced {len(existing_ids)} existing chunks for {filename}")
                else:
                    new_count += 1
                
                # Split document into chunks
                chunks = self.splitter.split_text(doc["content"])
                
                for i, chunk_text in enumerate(chunks):
                    chunk_id = f"{filename}_chunk_{i}"
                    
                    # Generate embedding explicitly
                    embedding = self.embeddings.embed_query(chunk_text)
                    
                    ids.append(chunk_id)
                    docs.append(chunk_text)
                    embeddings.append(embedding)
                    metadatas.append({
                        "filename": doc["filename"],
                        "chunk_index": i,
                        "source": doc["path"]
                    })
                    
                    # Tokenize for BM25 in parallel
                    tokenized = chunk_text.lower().split()
                    new_tokenized_docs.append(tokenized)
                    new_doc_ids.append(chunk_id)
                    
                    chunk_count += 1
            
            # Add all to ChromaDB in one batch
            if ids:
                self.collection.add(
                    ids=ids,
                    documents=docs,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            
            # Update BM25 index incrementally with new documents
            if new_tokenized_docs:
                self.bm25_corpus.extend(docs)
                self.bm25_corpus_ids.extend(new_doc_ids)
                
                # Rebuild BM25 with all documents (existing + new)
                all_tokenized = [doc.lower().split() for doc in self.bm25_corpus]
                self.bm25_index = BM25Okapi(all_tokenized)
                
                logger.info(f"BM25 index updated with {len(new_tokenized_docs)} new documents")
            
            logger.info(f"Ingested {chunk_count} chunks from {len(processed_filenames)} documents ({new_count} new, {replaced_count} replaced)")
            
            return {
                "chunk_count": chunk_count,
                "replaced_count": replaced_count,
                "new_count": new_count
            }
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            raise
    
    def _rebuild_bm25_index(self) -> None:
        """Rebuild BM25 index from all documents in ChromaDB."""
        try:
            # Get all documents from ChromaDB
            all_results = self.collection.get()
            
            if not all_results or not all_results.get("documents"):
                logger.info("No documents in ChromaDB, BM25 index empty")
                self.bm25_corpus = []
                self.bm25_corpus_ids = []
                self.bm25_index = None
                return
            
            # Tokenize documents for BM25 (simple whitespace + lowercase tokenization)
            documents = all_results["documents"]
            document_ids = all_results["ids"]
            
            # Tokenize: split by whitespace and convert to lowercase
            tokenized_docs = [doc.lower().split() for doc in documents]
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(tokenized_docs)
            self.bm25_corpus = documents
            self.bm25_corpus_ids = document_ids
            
            logger.info(f"BM25 index rebuilt with {len(documents)} documents")
        except Exception as e:
            logger.error(f"Error rebuilding BM25 index: {e}")
            self.bm25_index = None
    
    def _bm25_search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Tuple[str, float, str]]:
        """Perform BM25 sparse search."""
        try:
            if not self.bm25_index or not self.bm25_corpus:
                return []
            
            # Tokenize query
            query_tokens = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Get top-k results with scores
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            results = [
                (self.bm25_corpus[i], scores[i], self.bm25_corpus_ids[i]) 
                for i in top_indices if scores[i] > 0
            ]
            
            return results
        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range."""
        if not scores or len(scores) == 0:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if min_score == max_score:
            return [1.0] * len(scores)
        
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def _hybrid_search(
        self, 
        query: str, 
        top_k: int = TOP_K_RESULTS,
        alpha: float = 0.5
    ) -> List[Tuple[str, float]]:
        """Perform hybrid search combining BM25 and dense retrieval.
        
        Args:
            query: Search query
            top_k: Number of results to return
            alpha: Weight for dense search (0-1). Dense weight = alpha, BM25 weight = 1-alpha
                  0.0 = pure BM25, 1.0 = pure dense, 0.5 = equal weight
        
        Returns:
            List of (document, combined_score) tuples sorted by combined score
        """
        try:
            dense_results = []
            bm25_results = []
            
            # Get dense search results
            query_embedding = self.embeddings.embed_query(query)
            dense_search = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if dense_search and dense_search.get("documents"):
                dense_docs = dense_search["documents"][0]
                # ChromaDB returns distances, convert to similarity scores (1 / (1 + distance))
                dense_distances = dense_search.get("distances", [[]])[0]
                dense_scores = [1 / (1 + d) for d in dense_distances]
                
                # Normalize dense scores
                normalized_dense_scores = self._normalize_scores(dense_scores)
                dense_results = list(zip(dense_docs, normalized_dense_scores))
            
            # Get BM25 results
            bm25_results_raw = self._bm25_search(query, top_k)
            if bm25_results_raw:
                bm25_docs = [r[0] for r in bm25_results_raw]
                bm25_scores = [r[1] for r in bm25_results_raw]
                # Normalize BM25 scores
                normalized_bm25_scores = self._normalize_scores(bm25_scores)
                bm25_results = list(zip(bm25_docs, normalized_bm25_scores))
            
            # Combine results
            combined_scores = {}
            
            # Add dense search scores
            for doc, score in dense_results:
                combined_scores[doc] = alpha * score
            
            # Add BM25 scores
            for doc, score in bm25_results:
                if doc in combined_scores:
                    combined_scores[doc] += (1 - alpha) * score
                else:
                    combined_scores[doc] = (1 - alpha) * score
            
            # Sort by combined score and return top-k
            sorted_results = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]
            
            return sorted_results
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def rerank(self, query: str, docs: List[str]) -> List[tuple]:
        """Rerank documents based on relevance to query using cross-encoder."""
        pairs = [(query, doc) for doc in docs]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return ranked
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = TOP_K_RESULTS, use_hybrid: bool = True) -> List[str]:
        """Retrieve relevant document chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of results to retrieve before reranking
            use_hybrid: If True, use hybrid search (BM25 + dense). If False, use dense only.
        
        Returns:
            List of relevant document chunks
        """
        try:
            if use_hybrid:
                # Use hybrid search combining BM25 and dense retrieval
                hybrid_results = self._hybrid_search(query, top_k=top_k, alpha=0.5)
                if hybrid_results:
                    docs = [chunk for chunk, score in hybrid_results]
                else:
                    docs = []
            else:
                # Original dense-only search
                query_embedding = self.embeddings.embed_query(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                
                if results and results["documents"]:
                    docs = results["documents"][0]
                else:
                    docs = []
            
            # Rerank the retrieved chunks
            if docs:
                reranked_chunks = self.rerank(query, docs)
                return [chunk for chunk, score in reranked_chunks[:5]]  # return top 5
            return []
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []

    def generate_response(self, query: str, context_chunks: List[str]) -> str:
        """Generate response using LLM with retrieved context."""
        try:
            # Build augmented prompt with LangChain PromptTemplate
            context = "\n\n".join(context_chunks)
            prompt_template = PromptTemplate(
                template="""You are a helpful assistant. Use the following context to answer the question.
If the context doesn't contain relevant information, say so. Follow the steps below to generate your answer:
1. Read the context carefully.
2. If the context contains relevant information, use it to answer the question.
3. If the context does not contain relevant information, try to answer with you general knowledge, else respond with "I don't have enough information to answer this question."
4. Suggest the next best question to continue the conversation, if applicable.

Context:
{context}

Question: {query}

Answer:""",
                input_variables=["context", "query"]
            )
            prompt = prompt_template.format(context=context, query=query)
            
            # Generate response
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def query(self, question: str) -> dict:
        """Full RAG pipeline: retrieve and generate response."""
        try:
            # Retrieve relevant chunks
            context_chunks = self.retrieve_relevant_chunks(question)
            
            if not context_chunks:
                return {
                    "question": question,
                    "answer": "I don't have enough information to answer this question.",
                    "sources": []
                }
            
            # Generate response
            answer = self.generate_response(question, context_chunks)
            
            return {
                "question": question,
                "answer": answer,
                "sources": context_chunks[:2]  # Return top 2 sources
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            raise

    def clear_database(self):
        """Clear all documents from ChromaDB."""
        try:
            # Delete and recreate collection
            self.chroma_client.delete_collection(name="rag_documents")
            self.collection = self.chroma_client.get_or_create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Database cleared")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            raise
