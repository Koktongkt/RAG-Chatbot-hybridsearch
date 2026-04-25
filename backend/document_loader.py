import os
import logging
from pathlib import Path
import tempfile
from typing import List
from io import BytesIO
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from markitdown import MarkItDown
import pytesseract
from pdf2image import convert_from_bytes
from config import DOCUMENTS_DIR, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

class DocumentLoader:
    def extract_with_pypdf(self, pdf_bytes: bytes) -> str:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def extract_with_ocr(self, pdf_bytes: bytes) -> str:
        images = convert_from_bytes(pdf_bytes)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        return text

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n# ", # main sectrions
                "\n## ", # subsections
                "\n### ",
                "\n\n",
                "\n",
                " "]
        )
        self.md = MarkItDown()

    def load_pdf_from_bytes(self, pdf_bytes: bytes, filename: str) -> str:
        """Robust PDF extraction pipeline with fallback."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name

            # MARKITDOWN (PRIMARY)
            try:
                result = self.md.convert(temp_file_path)
                text = result.text_content

                if text and len(text.strip()) > 20:
                    logger.info(f"[MarkItDown SUCCESS] {filename}")
                    return text
                else:
                    raise ValueError("Empty or too short")

            except Exception as e:
                logger.warning(f"[MarkItDown FAILED] {filename}: {e}")

            # 2. PYPDF (FALLBACK)
            try:
                text = self.extract_with_pypdf(pdf_bytes)

                if text and len(text.strip()) > 100:
                    logger.info(f"[PyPDF SUCCESS] {filename}")
                    return text
                else:
                    raise ValueError("Empty or too short")

            except Exception as e:
                logger.warning(f"[PyPDF FAILED] {filename}: {e}")

            # 3. OCR (LAST RESORT)
            logger.warning(f"[OCR FALLBACK] {filename}")
            text = self.extract_with_ocr(pdf_bytes)

            if not text.strip():
                raise ValueError("OCR also failed")

            return text

        except Exception as e:
            logger.error(f"[TOTAL FAILURE] {filename}: {e}")
            raise

    def load_pdf_from_file(self, file_path: str) -> str:
        """Load and extract text from PDF file with fallback."""
        try:
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

            return self.load_pdf_from_bytes(pdf_bytes, os.path.basename(file_path))

        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise

    def load_all_documents(self) -> List[dict]:
        """Load all PDF documents from DOCUMENTS_DIR."""
        documents = []
        
        if not DOCUMENTS_DIR.exists():
            logger.warning(f"Documents directory not found: {DOCUMENTS_DIR}")
            return documents

        for file_path in DOCUMENTS_DIR.glob("*.pdf"):
            try:
                text = self.load_pdf_from_file(str(file_path))
                documents.append({
                    "filename": file_path.name,
                    "content": text,
                    "path": str(file_path)
                })
                logger.info(f"Loaded document: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to load {file_path.name}: {e}")
                continue

        logger.info(f"Loaded {len(documents)} documents")
        return documents

    def load_uploaded_documents(self, uploaded_files: List) -> List[dict]:
        """Load uploaded PDF files from file objects."""
        documents = []
        
        for file in uploaded_files:
            try:
                # Read file bytes
                file_bytes = file.read()
                filename = file.filename
                
                # Extract text
                text = self.load_pdf_from_bytes(file_bytes, filename)
                
                documents.append({
                    "filename": filename,
                    "content": text,
                    "path": f"uploaded:{filename}"
                })
                logger.info(f"Loaded uploaded document: {filename}")
            except Exception as e:
                logger.error(f"Failed to load uploaded {file.filename}: {e}")
                continue

        logger.info(f"Loaded {len(documents)} uploaded documents")
        return documents

    def chunk_documents(self, documents: List[dict]) -> List[dict]:
        """Split documents into chunks."""
        chunks = []
        
        for doc in documents:
            split_texts = self.splitter.split_text(doc["content"])
            for i, chunk_text in enumerate(split_texts):
                chunks.append({
                    "filename": doc["filename"],
                    "chunk_id": i,
                    "content": chunk_text,
                    "source": doc["path"],
                    "type": "markdown"
                })
        
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
