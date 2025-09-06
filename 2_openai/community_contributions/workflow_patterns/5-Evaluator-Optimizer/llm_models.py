# llm_model.py

import os
from typing import Dict, Optional

from agents import OpenAIChatCompletionsModel

# Import static configuration from configs.py
from configs import AVAILABLE_LLMS, LLMConfig
from dotenv import load_dotenv
from openai import AsyncOpenAI

print(f"INFO | Loading .env file success: {load_dotenv(override=True)}")


class LLM:
    """A simple container for a configured LLM model instance."""

    def __init__(self, provider: str, model: OpenAIChatCompletionsModel) -> None:
        self.provider: str = provider
        self.model: OpenAIChatCompletionsModel = model


class LLMManager:
    """
    Manages the creation and access of LLM instances.

    This class implements a factory and registry pattern. It creates LLMs
    on-demand (lazy instantiation) and caches them for future use.
    """

    def __init__(self, llm_registry: Dict[str, LLMConfig]) -> None:
        self._registry: Dict[str, LLMConfig] = llm_registry
        self._instances: Dict[str, LLM] = {}  # Cache for created instances

    def _create_llm_instance(self, provider) -> LLM:
        """Factory method to create a single LLM instance."""
        if provider not in self._registry:
            raise ValueError(
                f"Unsupported LLM provider: '{provider}'. Available providers: {list(self._registry.keys())}"
            )

        config: LLMConfig = self._registry[provider]

        # This is the single, generic way to create a client now.
        api_key: str | None = os.getenv(config.api_key_env_var)
        if not api_key:
            print(
                f"WARNING | API key environment variable '{config.api_key_env_var}' not set for provider '{provider}'. The model will not be available."
            )
            raise ValueError(f"API key for {provider} is not configured.")

        try:
            llm_client = AsyncOpenAI(
                base_url=config.base_url,
                api_key=api_key,
            )

            model_instance = OpenAIChatCompletionsModel(
                model=config.model_name, openai_client=llm_client
            )

            print(
                f"INFO | Successfully initialized LLM for provider: '{provider}' with model '{config.model_name}'."
            )
            return LLM(provider=provider, model=model_instance)

        except Exception as e:
            print(
                f"ERROR | Failed to create LLM instance for provider '{provider}': {e}"
            )
            raise  # Re-raise the exception after logging

    def get_llm(self, provider) -> Optional[LLM]:
        """
        Gets an LLM instance for a given provider.

        Uses a cached instance if available, otherwise creates a new one.
        Returns None if the instance cannot be created (e.g., missing API key).
        """
        if provider not in self._instances:
            try:
                # Lazy instantiation: create the instance only when first requested.
                self._instances[provider] = self._create_llm_instance(provider)
            except (ValueError, Exception):
                # If creation fails (e.g., missing key), we store None in the cache
                # to avoid retrying on subsequent calls and return it.
                self._instances[provider] = None

        return self._instances.get(provider)

    def get_model(self, provider) -> Optional[OpenAIChatCompletionsModel]:
        """Convenience method to directly get the underlying model."""
        llm_instance: LLM | None = self.get_llm(provider=provider)
        return llm_instance.model if llm_instance else None


# --- Global Singleton Instance ---
# Create a single manager instance that the rest of your application can use.
llm_manager = LLMManager(llm_registry=AVAILABLE_LLMS)

# gemini_llm: LLM | None = llm_manager.get_llm("gemini")
# gemini_model = gemini_llm.model

# or
# gemini_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("gemini")
# deepseek_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("deepseek")
# groq_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("groq")
