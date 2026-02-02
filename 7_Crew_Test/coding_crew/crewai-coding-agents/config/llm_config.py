"""
LLM Configuration and Factory
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from .settings import settings


@dataclass
class LLMConfig:
    """LLM configuration container"""
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    Factory function to create LLM instances
    
    Args:
        provider: LLM provider (openai, anthropic)
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens for response
    
    Returns:
        LangChain LLM instance
    """
    provider = provider or settings.default_llm_provider
    model = model or settings.default_llm_model
    temperature = temperature if temperature is not None else settings.default_temperature
    max_tokens = max_tokens or settings.default_max_tokens
    
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.openai_api_key
        )
    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.anthropic_api_key
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


# Predefined LLM configurations for different agent types
LLM_CONFIGS = {
    "manager": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.7,
        max_tokens=4096
    ),
    "coder": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.3,
        max_tokens=8192
    ),
    "analyst": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.5,
        max_tokens=4096
    ),
    "creative": LLMConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.8,
        max_tokens=4096
    )
}


def get_llm_for_role(role: str):
    """Get appropriate LLM for agent role"""
    config = LLM_CONFIGS.get(role, LLM_CONFIGS["coder"])
    return get_llm(
        provider=config.provider,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens
    )
