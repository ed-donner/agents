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
    # When the QA agent uses its whole call budget, ADK logs the call-limit as a node
    # failure traceback (from two places) before raising it; we catch and handle that
    # case, so those tracebacks are just noise on the console. A genuinely fatal error
    # still surfaces as a raised exception, so quieting these loggers only drops the
    # duplicate trace.
    for name in ("google_adk.google.adk.workflow._node_runner", "google_adk.google.adk.runners"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
