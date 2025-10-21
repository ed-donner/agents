@echo off
echo ============================================================
echo Starting WindowWolf Chatbot
echo ============================================================
echo.
echo The chatbot will open in your browser automatically...
echo If it doesn't open, visit: http://localhost:7860
echo.
echo Press Ctrl+C to stop the chatbot when done.
echo ============================================================
echo.

cd /d "%~dp0"
python 3_run_chatbot.py

pause

