# 🚀 Quick Start Guide - RAG Chatbot

## ✨ What's New!

**PDF Upload Feature** - You can now upload your own PDFs directly from the UI! The system will:
- Accept PDF file uploads
- Automatically extract text from PDFs
- Generate embeddings (using all-MiniLM-L6-v2)
- Append to the existing ChromaDB collection
- Make the content immediately searchable

## ✅ What's Been Built

Your complete RAG system is ready! Here's what was created:

### Backend Components ✨
- **app.py** - Flask API server with 4 endpoints:
  - `/health` - Health check
  - `/ingest` - Load PDFs and vectorize them
  - `/query` - Chat endpoint
  - `/clear` - Clear database

- **rag_engine.py** - RAG pipeline that:
  - Uses MXBAI embeddings for document chunks
  - Stores vectors in ChromaDB
  - Retrieves relevant chunks
  - Augments prompts with context
  - Generates responses using Ollama LLM

- **document_loader.py** - Processes PDF files:
  - Reads all PDFs from Documents/ folder
  - Chunks text into manageable pieces
  - Ready for embedding

- **config.py** - Centralized configuration

### Frontend Components 🎨
- **index.html** - Chat interface with:
  - Document ingestion button (Documents folder)
  - **NEW:** PDF upload button (custom documents)
  - Chat message display
  - Real-time message updates
  - Status indicators

- **styles.css** - Modern purple gradient theme with upload button styling
- **script.js** - Frontend logic with API integration + upload handler

### Configuration Files 🔧
- **requirements.txt** - All Python dependencies
- **.env** - Environment variables
- **start.bat** - Windows startup script
- **start.sh** - Linux/Mac startup script
- **SETUP.md** - Detailed setup guide

## 📋 Next Steps

### 1. Install Ollama (if not already installed)
```
Download from: https://ollama.ai
```

### 2. Start Ollama Server
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull required models
ollama pull gemma2:26b
ollama pull mxbai-embed-large
```

### 3. Run the RAG Application

**Windows**:
```bash
start.bat
```

**Linux/Mac**:
```bash
bash start.sh
```

### 4. Access the Web Interface
```
Open: http://localhost:5000
```

### 5. Use the System
1. **Option A:** Click "📥 Ingest Documents" to load PDFs from Documents folder
2. **Option B:** Click "📤 Upload PDF" to add your own PDFs (can select multiple)
3. Wait for completion
4. Type a question: "What are my resume highlights?"
5. Get AI-powered answers!

## 🆕 PDF Upload Feature

### Upload Single or Multiple PDFs
- Click "📤 Upload PDF"
- Select one or more PDF files
- System automatically:
  - Extracts text from all PDFs
  - Splits into chunks (500 tokens with 100 token overlap)
  - Generates embeddings with all-MiniLM-L6-v2
  - Appends to ChromaDB collection
  - Shows progress in chat

### Key Features
- ✅ Upload multiple PDFs at once
- ✅ Appends to existing collection (doesn't replace)
- ✅ Validates file types (PDF only)
- ✅ Real-time processing feedback
- ✅ Automatic error handling

## 🎯 How It Works

### Ingestion Pipeline (Upload or Ingest)
```
PDF File(s)
     ↓
Text Extraction
     ↓
Text Chunking (500 tokens)
     ↓
Embedding Generation (all-MiniLM-L6-v2)
     ↓
ChromaDB Storage (appends to collection)
```

### Query Pipeline
```
User Question
     ↓
Query Engine (RAG)
     ├→ Get embedding
     ├→ Search ChromaDB
     ├→ Retrieve top 3 chunks
     ↓
LLM (Ollama gemma2:26b)
     ├→ Augment prompt with context
     ├→ Generate response
     ↓
Chat Interface
     └→ Display answer + sources
```

## 📚 Example Questions to Try

After uploading or ingesting PDFs:
- "What are the key achievements in the resume?"
- "Summarize the assessment results"
- "What skills are mentioned?"
- "Tell me about the professional experience"
- "What are the main themes?"
- "Extract the important dates"
- "Summarize this document"

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure Ollama is running: `ollama serve` |
| "Model not found" | Pull model: `ollama pull gemma2:26b` |
| "CORS error in browser" | Backend must be running on port 5000 |
| "Slow responses" | First query loads model. Subsequent queries are faster. |

## 📊 Project Status

| Component | Status |
|-----------|--------|
| Project setup | ✅ Done |
| Python dependencies | ✅ Installed |
| Document pipeline | ✅ Done |
| PDF upload support | ✅ NEW! |
| RAG engine | ✅ Done |
| Flask API | ✅ Done |
| Web frontend | ✅ Done |
| Testing | ⏳ Ready to test |

## 💡 Tips

1. **First query is slower** - The LLM is loading into memory
2. **Multiple uploads** - You can upload multiple PDFs at once
3. **Append mode** - Uploads append to existing collection (don't clear database)
4. **Customize chunk size** - Change `CHUNK_SIZE` in `backend/config.py` for better results
5. **All-MiniLM-L6-v2** - Lightweight embeddings (384 dims), fast and accurate, can switch to ollama/mxbai-embed-large with 1024 dims
6. **Clear when needed** - Use "🗑️ Clear Database" to start fresh

## 🎓 Key Technologies

- **LangChain** - RAG orchestration
- **ChromaDB** - Vector storage
- **Ollama** - Local LLM inference
- **MXBAI** - Semantic embeddings
- **Flask** - Web API
- **Vanilla JS** - Frontend

---

**Ready to chat?** Start with `start.bat` (Windows) or `bash start.sh` (Linux/Mac)

Questions? Check SETUP.md for detailed documentation.
