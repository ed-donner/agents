"""A local concierge that delegates translation to a remote A2A agent.

RemoteA2aAgent reads the remote agent's card and then behaves like a local
sub-agent. The concierge does the talking and hands translation work to the
remote translator over A2A. Drive it with `adk web .` from the a2a_demo folder.
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
from google.adk.agents.remote_a2a_agent import (  # noqa: E402
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)

# The full card URL. RemoteA2aAgent uses the string as given, so build it by
# joining the base with the well-known path rather than passing a bare host.
translator = RemoteA2aAgent(
    name="translator_agent",
    description="Remote agent that translates English into Spanish.",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
    use_legacy=False,
)

root_agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="spanish_concierge",
    description="A concierge that answers in Spanish by delegating translation.",
    instruction=(
        "When the user wants something translated into Spanish, delegate to "
        "translator_agent and return its result."
    ),
    sub_agents=[translator],
)
