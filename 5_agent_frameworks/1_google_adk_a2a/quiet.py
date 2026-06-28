"""Turn down library chatter so the agent's own trace is easy to read.

ADK prints a handful of [EXPERIMENTAL] feature notices, and google-genai logs a
line every time it sees both GOOGLE_API_KEY and GEMINI_API_KEY in the
environment (harmless, left over from the CrewAI week). None of it is ours to
act on, so we quiet it. Call silence() before importing ADK.
"""

import logging
import warnings


def silence() -> None:
    warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*")
    logging.getLogger("google_genai._api_client").setLevel(logging.ERROR)
