"""Configurable chat model router: OpenAI, Anthropic, DeepSeek, Ollama."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from rich.console import Console

console = Console()

# Load env from project dir and repo root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"), override=False)
load_dotenv(os.path.join(_ROOT, "..", "..", "..", "..", ".env"), override=False)


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _build_openai(model: str, **kwargs: Any) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model, temperature=0.2, **kwargs)


def _build_anthropic(model: str, **kwargs: Any) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=model, temperature=0.2, **kwargs)


def _build_deepseek(model: str, **kwargs: Any) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    key = _env("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY is required for DeepSeek")
    return ChatOpenAI(
        model=model,
        api_key=key,
        base_url="https://api.deepseek.com/v1",
        temperature=0.2,
        **kwargs,
    )


def _build_ollama(model: str, **kwargs: Any) -> BaseChatModel:
    from langchain_community.chat_models import ChatOllama

    base = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    return ChatOllama(model=model, base_url=base, temperature=0.2, **kwargs)


def chat_model_for_role(role: str) -> BaseChatModel:
    """
    Optional per-role overrides (multiple providers in one session):
      LLM_PROVIDER_RESEARCH, LLM_MODEL_RESEARCH
      LLM_PROVIDER_PRO, LLM_MODEL_PRO
      LLM_PROVIDER_AGAINST, LLM_MODEL_AGAINST
      LLM_PROVIDER_JUDGE, LLM_MODEL_JUDGE
    Falls back to LLM_PROVIDER / LLM_MODEL.
    """
    key = role.strip().upper()
    p = _env(f"LLM_PROVIDER_{key}") or None
    m = _env(f"LLM_MODEL_{key}") or None
    return build_chat_model(provider=p, model=m)


def build_chat_model(
    provider: str | None = None,
    model: str | None = None,
) -> BaseChatModel:
    """
    Factory for LangChain chat models.

    Environment:
      LLM_PROVIDER: openai | claude | deepseek | ollama
      LLM_MODEL: e.g. gpt-4o-mini, claude-sonnet-4-20250514, deepseek-chat, llama3.2
    """
    prov = (provider or _env("LLM_PROVIDER", "openai")).lower()
    mdl = model or _env("LLM_MODEL", "")

    builders = {
        "openai": lambda: _build_openai(
            mdl or "gpt-4o-mini",
        ),
        "gpt": lambda: _build_openai(mdl or "gpt-4o-mini"),
        "claude": lambda: _build_anthropic(
            mdl or "claude-sonnet-4-20250514",
        ),
        "anthropic": lambda: _build_anthropic(mdl or "claude-sonnet-4-20250514"),
        "deepseek": lambda: _build_deepseek(mdl or "deepseek-chat"),
        "ollama": lambda: _build_ollama(mdl or "llama3.2"),
        "llama": lambda: _build_ollama(mdl or "llama3.2"),
    }

    if prov not in builders:
        raise ValueError(f"Unknown LLM_PROVIDER: {prov}")

    try:
        return builders[prov]()
    except Exception as exc:  # noqa: BLE001
        if prov == "ollama":
            raise
        console.print(
            f"[yellow]Primary LLM ({prov}) unavailable ({exc}); trying Ollama fallback.[/yellow]"
        )
        return _build_ollama(_env("OLLAMA_FALLBACK_MODEL", "llama3.2"))


class LLMRouter:
    """Small facade matching the requested API style (e.g. LLMRouter(model=\"claude\"))."""

    _ALIASES: dict[str, tuple[str, str]] = {
        "gpt-4": ("openai", "gpt-4o"),
        "gpt-4o": ("openai", "gpt-4o"),
        "gpt-4o-mini": ("openai", "gpt-4o-mini"),
        "claude": ("claude", "claude-sonnet-4-20250514"),
        "deepseek": ("deepseek", "deepseek-chat"),
        "llama3": ("ollama", "llama3.2"),
        "llama3.2": ("ollama", "llama3.2"),
    }

    def __init__(self, model: str | None = None, provider: str | None = None) -> None:
        if model and provider is None:
            key = model.lower().strip()
            if key in self._ALIASES:
                self.provider, self.model = self._ALIASES[key]
            else:
                self.provider = None
                self.model = model
        else:
            self.provider = provider
            self.model = model
        self._llm: BaseChatModel | None = None

    @property
    def llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = build_chat_model(
                provider=self.provider,
                model=self.model,
            )
        return self._llm

    def refresh(self) -> None:
        self._llm = build_chat_model(provider=self.provider, model=self.model)

    def __repr__(self) -> str:
        return f"LLMRouter(provider={self.provider!r}, model={self.model!r})"
