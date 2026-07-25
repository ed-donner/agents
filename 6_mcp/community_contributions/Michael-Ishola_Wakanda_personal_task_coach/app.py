import argparse

from config import APP_DIR
from coach import TaskCoach
from ui import CoachingView


def run_ui() -> None:
    coach = TaskCoach(APP_DIR)
    app = CoachingView(coach).build()
    app.launch(inbrowser=True)


def main() -> None:
    run_ui()


if __name__ == "__main__":
    main()
