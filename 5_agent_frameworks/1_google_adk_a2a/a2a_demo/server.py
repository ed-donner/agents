"""Expose a translator agent as an A2A service.

`to_a2a` wraps an ordinary ADK agent in a Starlette app that serves an agent
card and answers A2A requests. Run it with uvicorn:

    uvicorn server:a2a_app --host localhost --port 8001

The port you pass to to_a2a is what the agent card advertises, so it must match
the uvicorn --port.
"""

import logging
import os
import warnings

from dotenv import load_dotenv

warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*")
logging.getLogger("google_genai._api_client").setLevel(logging.ERROR)

load_dotenv(override=True)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.a2a.utils.agent_to_a2a import to_a2a  # noqa: E402

root_agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="translator_agent",
    description="Translates English text into Spanish.",
    instruction=(
        "Translate the user's English text into natural Spanish. "
        "Reply with only the Spanish translation and nothing else."
    ),
)

# Returns a Starlette ASGI app. The port here is what the agent card advertises.
a2a_app = to_a2a(root_agent, port=8001)
