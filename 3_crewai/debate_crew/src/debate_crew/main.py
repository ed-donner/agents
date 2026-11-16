

#!/usr/bin/env python

import sys
from pathlib import Path
from datetime import datetime

from debate_crew.crew import DebateCrew
from debate_crew.validator import correct_verdict_consistency, validate_verdict_file


def run():
    """Run the debate crew and validate its verdict."""

    # Read the debate motion from command-line arguments.
    motion = " ".join(sys.argv[1:]).strip()

    if not motion:
        motion = "Artificial intelligence will improve education."

    # Prepare the inputs for CrewAI.
    inputs = {
        "motion": motion,
        "current_year": str(datetime.now().year),
    }

    # Execute the existing sequential debate workflow.
    result = DebateCrew().crew().kickoff(inputs=inputs)

    # Display the generated verdict.
    print("\n========== DEBATE VERDICT ==========\n")
    print(result)

    # Correct reported totals and winner from valid table scores.
    verdict_path = Path("debate_verdict.md")
    if verdict_path.is_file():
        original_text = verdict_path.read_text(encoding="utf-8")
        try:
            corrected_text = correct_verdict_consistency(original_text)
        except ValueError as exc:
            print(f"Automatic consistency correction skipped: {exc}")
        else:
            if corrected_text != original_text:
                verdict_path.write_text(corrected_text, encoding="utf-8")
                print("Corrected verdict totals/winner from the scoring table.")

    # Validate the saved verdict file.
    errors = validate_verdict_file("debate_verdict.md")

    if errors:
        print("\n========== VERDICT VALIDATION FAILED ==========\n")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print("\n========== VERDICT VALIDATION PASSED ==========\n")
    print("All configured verdict checks passed.")


if __name__ == "__main__":
    run()
