"""Run the research crew. Usage: uv run python main.py "your topic" """
import sys

from dotenv import load_dotenv

from crew import ResearchCrew

load_dotenv(override=True)


def run():
    topic = " ".join(sys.argv[1:]) or "the current state of agentic AI frameworks"
    result = ResearchCrew().crew().kickoff(inputs={"topic": topic})
    print(result)


if __name__ == "__main__":
    run()
