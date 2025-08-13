@echo off
echo ========================================
echo Transcript Summarizer - Quick Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate virtual environment and install dependencies
echo.
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip

echo.
echo Installing from requirements.txt (this may take a few minutes)...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Full installation failed. Trying minimal installation...
    pip install -r requirements-minimal.txt
    if errorlevel 1 (
        echo ❌ Installation failed. Please check the error messages above.
        pause
        exit /b 1
    ) else (
        echo ✅ Minimal installation completed successfully!
        echo Note: Some advanced features may not work with minimal installation.
    )
) else (
    echo ✅ Full installation completed successfully!
)

REM Check if Ollama is running
echo.
echo Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama is not running
    echo Please start Ollama with: ollama serve
    echo Then pull the model with: ollama pull llama3.1:8b
) else (
    echo ✅ Ollama is running
)

echo.
echo ========================================
echo Testing Installation...
echo ========================================
python test_installation.py

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo 1. Make sure Ollama is running: ollama serve
echo 2. Make sure LLaMA3 is installed: ollama pull llama3.1:8b
echo 3. Run: python main.py
echo 4. Open http://localhost:7860 in your browser
echo.
echo For Docker setup, run:
echo docker-compose -f docker/docker-compose.yml up --build
echo.
echo To test your installation anytime, run:
echo python test_installation.py
echo.
pause
