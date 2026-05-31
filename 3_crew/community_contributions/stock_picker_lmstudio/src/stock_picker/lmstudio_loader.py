import lmstudio as lms
import os
import requests
from typing import List, Union
from dotenv import load_dotenv

class LMStudioManager:
    def __init__(self):
        load_dotenv(override=True)

        self.SERVER_API_HOST = os.getenv("SERVER_API_HOST")
        print(f"[INFO] LM Studio API Host: {self.SERVER_API_HOST}")
        self.API_KEY = os.getenv("API_KEY")
        print(f"[INFO] LM Studio API Key: {'Found' if self.API_KEY else 'Not Found'}")

        self.model = None
        self.model_name = None

        self.embedding_model = os.getenv(
            "EMBEDDING_MODEL",
            "text-embedding-nomic-embed-text-v1.5"
        )

        self._ensure_model_loaded()

    def _ensure_model_loaded(self):
        # Check already loaded models
        loaded_models = lms.list_loaded_models("llm")

        if loaded_models:
            self.model_name = loaded_models[0].identifier
            print(f"[INFO] Using already loaded model: {self.model_name}")

        else:
            print("[INFO] No model currently loaded.")

            downloaded_models = lms.list_downloaded_models("llm")

            if not downloaded_models:
                raise Exception("No downloaded LLM models found in LM Studio.")

            # Auto-load if only one
            if len(downloaded_models) == 1:
                self.model_name = downloaded_models[0].model_key
                print(f"[INFO] Only one model found. Loading: {self.model_name}")

            else:
                print("\nAvailable downloaded models:\n")
                for i, model in enumerate(downloaded_models):
                    print(f"{i + 1}. {model.model_key}")

                while True:
                    try:
                        choice = int(input("\nSelect a model by number: "))
                        if 1 <= choice <= len(downloaded_models):
                            self.model_name = downloaded_models[choice - 1].model_key
                            break
                        else:
                            print("Invalid choice. Try again.")
                    except ValueError:
                        print("Please enter a valid number.")

            print(f"[INFO] Loading model: {self.model_name}")
            self.model = lms.llm(self.model_name)

        # Ensure model handle exists
        if not self.model:
            self.model = lms.llm(self.model_name)

_manager = LMStudioManager()

MODEL = _manager.model_name
EMBEDDING_MODEL = _manager.embedding_model
API_KEY = _manager.API_KEY
SERVER_API_HOST = _manager.SERVER_API_HOST

CREWAI_EMBEDDING_CONFIG = {
        "provider": "openai",
        "config": {
            "api_key": API_KEY,
            "api_base": SERVER_API_HOST,
            "model": EMBEDDING_MODEL
        }
    }