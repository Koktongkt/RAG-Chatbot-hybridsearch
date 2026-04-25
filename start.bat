@echo off
REM RAG Application Startup Script for Windows

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         Free Full Stack RAG - Application Startup              ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo ⚠️  IMPORTANT: Before running the app, ensure:
echo.
echo 1. Ollama is installed and running locally
echo    - Download from: https://ollama.ai
echo    - Start Ollama: ollama serve
echo.
echo 2. Pull the required models:
echo    - ollama pull gemma2:26b
echo    - ollama pull mxbai-embed-large
echo.
echo 3. Verify Ollama is running on http://localhost:11434
echo.
echo Starting Flask backend on http://localhost:5000
echo.

REM Start backend
cd backend
python app.py

pause
