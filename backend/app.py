import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from document_loader import DocumentLoader
from rag_engine import RAGEngine
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Get frontend directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Configure uploads
UPLOAD_FOLDER = Path(__file__).parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize RAG components
rag_engine = None
doc_loader = DocumentLoader()

@app.before_request
def initialize_rag():
    """Initialize RAG engine on first request."""
    global rag_engine
    if rag_engine is None:
        try:
            rag_engine = RAGEngine()
            logger.info("RAG Engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            return jsonify({"error": "Failed to initialize RAG Engine"}), 500

@app.route('/')
def index():
    """Serve the frontend."""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS)."""
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/ingest', methods=['POST'])
def ingest():
    """Ingest documents into the RAG system."""
    try:
        # Load all documents from Documents directory
        documents = doc_loader.load_all_documents()
        
        if not documents:
            return jsonify({"error": "No documents found"}), 400
        
        # Ingest into RAG engine
        result = rag_engine.ingest_documents(documents)
        
        # Build message based on results
        messages = []
        if result["new_count"] > 0:
            messages.append(f"Added {result['new_count']} new documents")
        if result["replaced_count"] > 0:
            messages.append(f"Replaced {result['replaced_count']} existing documents")
        
        message = f"Ingested {len(documents)} documents with {result['chunk_count']} chunks"
        if messages:
            message += f" ({', '.join(messages)})"
        
        return jsonify({
            "status": "success",
            "message": message,
            "documents_count": len(documents),
            "chunks_count": result["chunk_count"],
            "new_count": result["new_count"],
            "replaced_count": result["replaced_count"]
        }), 200
    except Exception as e:
        logger.error(f"Error in /ingest: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    """Upload and ingest PDF files."""
    try:
        # Check if files are provided
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({"error": "No files selected"}), 400
        
        # Validate files
        for file in files:
            if not allowed_file(file.filename):
                return jsonify({"error": f"Invalid file type: {file.filename}. Only PDF files allowed."}), 400
        
        # Load uploaded documents
        documents = doc_loader.load_uploaded_documents(files)
        
        if not documents:
            return jsonify({"error": "Failed to process uploaded files"}), 400
        
        # Ingest into RAG engine (append to existing collection)
        result = rag_engine.ingest_documents(documents)
        
        # Build message based on results
        messages = []
        if result["new_count"] > 0:
            messages.append(f"Added {result['new_count']} new documents")
        if result["replaced_count"] > 0:
            messages.append(f"Replaced {result['replaced_count']} existing documents")
        
        message = f"Uploaded and ingested {len(documents)} documents with {result['chunk_count']} chunks"
        if messages:
            message += f" ({', '.join(messages)})"
        
        return jsonify({
            "status": "success",
            "message": message,
            "documents_count": len(documents),
            "chunks_count": result["chunk_count"],
            "new_count": result["new_count"],
            "replaced_count": result["replaced_count"]
        }), 200
    except Exception as e:
        logger.error(f"Error in /upload: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query():
    """Query the RAG system."""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({"error": "Missing 'question' in request body"}), 400
        
        question = data['question'].strip()
        
        if not question:
            return jsonify({"error": "Question cannot be empty"}), 400
        
        # Process query through RAG
        result = rag_engine.query(question)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error in /query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear():
    """Clear all documents from the database."""
    try:
        rag_engine.clear_database()
        return jsonify({"status": "success", "message": "Database cleared"}), 200
    except Exception as e:
        logger.error(f"Error in /clear: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info(f"Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
