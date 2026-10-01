#!/usr/bin/env python
import os
import re
from dotenv import load_dotenv

from crew import Poster

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"), override=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_output(content, topic):
    """Persist the generated content to a markdown file in the outputs folder."""
    safe_topic = re.sub(r"[^a-zA-Z0-9._-]+", "_", topic).strip("_") or "linkedin_post"
    output_path = os.path.join(OUTPUT_DIR, f"{safe_topic}.md")
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return output_path


def run():
    """Run the LinkedIn post generation crew."""
    topic = input("Topic: ").strip()
    inputs = {
        "topic": topic,
    }
    try:
        result = Poster().crew().kickoff(inputs=inputs)
        content = getattr(result, "raw", str(result))
        print(content)
        output_path = save_output(content, topic)
        print(f"\nSaved output to: {output_path}")
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


if __name__ == "__main__":
    run()
