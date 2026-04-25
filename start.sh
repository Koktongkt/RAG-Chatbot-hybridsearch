#!/bin/bash

# RAG Application Startup Script for Linux/Mac

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Free Full Stack RAG - Application Startup              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "⚠️  IMPORTANT: Before running the app, ensure:"
echo ""
echo "1. Ollama is installed and running locally"
echo "   - Download from: https://ollama.ai"
echo "   - Start Ollama: ollama serve"
echo ""
echo "2. Pull the required models:"
echo "   - ollama pull gemma2:26b"
echo "   - ollama pull mxbai-embed-large"
echo ""
echo "3. Verify Ollama is running on http://localhost:11434"
echo ""
echo "Starting Flask backend on http://localhost:5000"
echo ""

# Start backend
cd backend
python app.py
