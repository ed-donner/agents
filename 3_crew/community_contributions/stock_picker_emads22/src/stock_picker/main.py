#!/usr/bin/env python
import sys
import warnings


from stock_picker.crew import StockPicker

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    inputs = {
        "sector": "Technology",
    }

    try:
        # Create and run the crew
        result = StockPicker().crew().kickoff(inputs=inputs)

        # Print the result
        print("\n\n=== FINAL DECISION ===\n\n")
        print(result.raw)

    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "sector": "Technology",
    }
    try:
        StockPicker().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        StockPicker().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "sector": "Technology",
    }

    try:
        StockPicker().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


# ------------------------------------------------------------
# NOTE:
# Running `crewai run` DOES NOT execute this block.
# The CrewAI CLI directly looks for the @crew function
# defined in your project (e.g., in crew.py) and runs
# the workflow from there.
#
# This conditional block is executed only when this file
# is run directly using "python main.py" and NOT when
# it's imported as a module. It's useful for:
# - Local testing
# - Debugging
# - Manually calling run, train, replay, or test functions
# without depending on the CrewAI CLI.
#
# This allows us to execute different functions (run, train,
# replay, test) from the command line for debugging or manual runs,
# without interfering with CrewAI's CLI commands.
#
# Examples:
#   python main.py               → runs the crew
#   python main.py train 5 file.json  → trains for 5 iterations and saves results
#   python main.py replay 12345  → replays a specific task
#   python main.py test 3 gpt-4  → runs test mode
# ------------------------------------------------------------
if __name__ == "__main__":
    # If the user passed at least one argument, check what it is
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "train":
            train()
        elif command == "replay":
            replay()
        elif command == "test":
            test()
        else:
            # Default to running the crew if the command is unrecognized
            run()
    else:
        # If no arguments are given, just run the crew normally
        run()
