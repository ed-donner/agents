import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from education_coach.app import launch_local  # noqa: E402

if __name__ == "__main__":
    launch_local()
