# load all the env and extra configs and the swet defaults

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)


def get_config() -> dict:

    config = {
        "firstname": "Elijah",
        "name": "Elijah HAASTRUP",
        "openrouter_url": "https://openrouter.ai/api/v1",
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "pushover_user": os.getenv("PUSHOVER_USER"),
        "pushover_token": os.getenv("PUSHOVER_TOKEN"),
        "pushover_url": "https://api.pushover.net/1",
    }

    return config