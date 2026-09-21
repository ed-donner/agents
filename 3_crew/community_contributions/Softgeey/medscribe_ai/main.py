"""
MedScribe AI — Entry Point
Run the web application:  python main.py
"""

from pathlib import Path
from src.config import get_flask_secret, is_debug
from app import app

if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print("=" * 50)
    print(" MedScribe AI — Discharge Summary Generator")
    print("=" * 50)
    print(" Open http://localhost:5000 in your browser")
    print(" Press Ctrl+C to stop")
    print("=" * 50)
    app.run(debug=is_debug(), host="0.0.0.0", port=5000)
