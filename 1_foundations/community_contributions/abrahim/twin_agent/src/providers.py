# AI Providers
import os
from dotenv import load_dotenv

class AiProvider:
    def __init__(self):
        load_dotenv(override=True)

        self.providers = {
            "foundry": {
                "endpoint": os.getenv("AZURE_FOUNDRY_ENDPOINT"),
                "api_key": os.getenv("AZURE_FOUNDRY_API_KEY"),
            },
            "groq": {
                "endpoint": os.getenv("GROQ_ENDPOINT"),
                "api_key": os.getenv("GROQ_API_KEY"),
            },
            "openrouter": {
                "endpoint": os.getenv("OPENROUTER_ENDPOINT"),
                "api_key": os.getenv("OPENROUTER_API_KEY"),
            },
        }

    def get_provider_credentials(self, provider_name):
        provider = self.providers.get(provider_name, None)
        false = False, "", ""
        if provider:
            endpoint = provider.get("endpoint", "")
            api_key = provider.get("api_key", "")
            if endpoint == "" or api_key == "":
                return false
            return True, endpoint, api_key
        return false
