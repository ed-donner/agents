#!/usr/bin/env python
import sys
import warnings

from content_creator.crew import ContentCreator

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the content creator crew.
    """
    inputs = {
        'topic': 'How AI agents are changing the way software gets built',
        'audience': 'software developers who are curious about AI but haven\'t used agents yet',
        'tone': 'conversational but authoritative',
    }

    try:
        result = ContentCreator().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """Train the crew for a given number of iterations."""
    inputs = {
        'topic': 'How AI agents are changing the way software gets built',
        'audience': 'software developers who are curious about AI but haven\'t used agents yet',
        'tone': 'conversational but authoritative',
    }
    try:
        ContentCreator().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        ContentCreator().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and return the results."""
    inputs = {
        'topic': 'How AI agents are changing the way software gets built',
        'audience': 'software developers who are curious about AI but haven\'t used agents yet',
        'tone': 'conversational but authoritative',
    }
    try:
        ContentCreator().crew().test(
            n_iterations=int(sys.argv[1]),
            openai_model_name=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
