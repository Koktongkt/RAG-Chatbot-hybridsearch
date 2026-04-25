# Free Full Stack RAG Application

A complete local Retrieval-Augmented Generation (RAG) system with:
- **Backend**: Python with LangChain, ChromaDB, and Ollama
- **Frontend**: Modern web interface for chat
- **Embeddings**: MXBAI for document vectorization
- **LLM**: Local Ollama models (gemma2:26b default)

## Quick Start

### Prerequisites
1. **Ollama** - Download from https://ollama.ai
2. **Python 3.8+**
3. Required Ollama models installed

### Installation

1. **Download and run Ollama**:
   ```bash
   # Start Ollama service
   ollama serve
   
   # In another terminal, pull required models
   ollama pull gemma2:26b
   ollama pull mxbai-embed-large
   ```

2. **Run the RAG application**:
   
   **Windows**:
   ```bash
   start.bat
   ```
   
   **Linux/Mac**:
   ```bash
   bash start.sh
   ```

3. **Access the web interface**:
   - Open browser to `http://localhost:5000`
   - Ensure backend is running before using frontend

## Project Structure

```
.
├── backend/
│   ├── app.py                 # Flask API server
│   ├── config.py              # Configuration
│   ├── document_loader.py     # PDF document loading
│   ├── rag_engine.py          # RAG pipeline
│   └── data/                  # ChromaDB storage
├── frontend/
│   ├── index.html             # Web interface
│   ├── styles.css             # Styling
│   └── script.js              # Client-side logic
├── Documents/                 # Place your PDFs here
├── requirements.txt           # Python dependencies
├── .env                       # Configuration
├── start.bat                  # Windows startup script
└── start.sh                   # Linux/Mac startup script
```

## Usage

1. **Ingest Documents**:
   - Click "📥 Ingest Documents" button
   - All PDFs in `Documents/` folder will be processed
   - Documents are split into chunks and vectorized

2. **Ask Questions**:
   - Type your question in the chat input
   - Press Enter or click Send
   - System retrieves relevant document chunks and generates answer
   - Sources are displayed for reference

3. **Clear Database**:
   - Click "🗑️ Clear Database" to remove all ingested documents
   - Useful when switching to different documents

## API Endpoints

- `GET /health` - Health check
- `POST /ingest` - Ingest documents from Documents/ folder
- `POST /query` - Query the RAG system
- `POST /clear` - Clear database

## Configuration

Edit `.env` file to customize:
- `FLASK_PORT` - Backend port (default: 5000)
- `LLM_MODEL` - Ollama model to use (default: gemma2:26b)
- `EMBEDDING_MODEL` - Embedding model (default: mxbai-embed-large)
- `CHUNK_SIZE` - Document chunk size (default: 500)
- `TOP_K_RESULTS` - Number of chunks to retrieve (default: 3)

## Available Ollama Models

Popular models for RAG:
- `gemma2:26b` - Fast, good quality (recommended)
- `mistral` - Smaller, fast
- `neural-chat` - Conversational
- `llama2` - General purpose
- `phi` - Ultra-lightweight

Pull additional models with: `ollama pull <model-name>`

## Troubleshooting

**"Failed to connect to Ollama"**:
- Ensure Ollama is running: `ollama serve`
- Check Ollama address in `.env`: `OLLAMA_BASE_URL=http://localhost:11434`

**"Model not found"**:
- Pull the model: `ollama pull gemma2:26b`
- Verify with: `ollama list`

**"CORS errors in browser"**:
- Backend is likely not running
- Verify backend is accessible: `curl http://localhost:5000/health`

**Slow responses**:
- First query is slower (model loading)
- Larger `TOP_K_RESULTS` = slower but more context
- Consider using a smaller model in `.env`

## Performance Tips

1. Use smaller models for faster responses:
   - `mistral` for speed
   - `gemma2:26b` for quality (balanced)
   - `llama2` for accuracy

2. Reduce `CHUNK_SIZE` in `.env` for faster retrieval
3. Reduce `TOP_K_RESULTS` for fewer API calls

## License

Free to use and modify.

## Support

For issues or questions, check:
1. Ollama is running: `http://localhost:11434`
2. Models are installed: `ollama list`
3. Python dependencies: `pip list`
4. Backend logs for errors
