import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from education_coach.app import create_demo  # noqa: E402

demo = create_demo()
