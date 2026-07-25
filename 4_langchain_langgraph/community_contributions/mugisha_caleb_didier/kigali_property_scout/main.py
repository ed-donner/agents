"""Kigali Property Scout — entry point"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(override=True)

from ui.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.launch(inbrowser=True)
