from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from .config import ArenaConfig, ModelSpec


@dataclass(slots=True)
class LLMResult:
    text: str
    model: str
    provider: str
    latency_ms: int
    fallback_used: bool = False


class ModelRouter:
    def __init__(self, config: ArenaConfig) -> None:
        self.config = config
        self._http = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._http.close()

    def _provider_config(self, provider: str) -> tuple[str, dict[str, str]]:
        provider = provider.lower()
        if provider == "groq":
            if not self.config.groq_api_key:
                raise RuntimeError("GROQ_API_KEY missing.")
            return (
                "https://api.groq.com/openai/v1/chat/completions",
                {
                    "Authorization": f"Bearer {self.config.groq_api_key}",
                    "Content-Type": "application/json",
                },
            )
        if provider == "anthropic":
            if not self.config.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY missing.")
            return (
                "https://api.anthropic.com/v1/messages",
                {
                    "x-api-key": self.config.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
            )
        if provider == "openrouter":
            if not self.config.openrouter_api_key:
                raise RuntimeError("OPENROUTER_API_KEY missing.")
            headers = {
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
                "X-Title": self.config.openrouter_app_name,
            }
            if self.config.openrouter_site_url:
                headers["HTTP-Referer"] = self.config.openrouter_site_url
            return ("https://openrouter.ai/api/v1/chat/completions", headers)
        raise RuntimeError(f"Unsupported provider '{provider}'.")

    @staticmethod
    def _normalize_anthropic_messages(
        messages: list[dict[str, str]],
    ) -> tuple[str | None, list[dict[str, str]]]:
        system_parts: list[str] = []
        normalized: list[dict[str, str]] = []
        for msg in messages:
            role = str(msg.get("role", "user")).strip().lower()
            content = str(msg.get("content", ""))
            if not content:
                continue
            if role == "system":
                system_parts.append(content)
                continue
            if role not in {"user", "assistant"}:
                role = "user"
            normalized.append({"role": role, "content": content})
        if not normalized:
            normalized = [{"role": "user", "content": "Continue."}]
        system = "\n\n".join(system_parts).strip() if system_parts else None
        return system, normalized

    def _chat_anthropic(
        self,
        model_spec: ModelSpec,
        messages: list[dict[str, str]],
        temperature: float,
        timeout_seconds: float,
    ) -> LLMResult:
        endpoint, headers = self._provider_config("anthropic")
        system, normalized = self._normalize_anthropic_messages(messages)
        payload: dict[str, Any] = {
            "model": model_spec.model,
            "max_tokens": 900,
            "temperature": temperature,
            "messages": normalized,
        }
        if system:
            payload["system"] = system
        response = self._http.post(endpoint, headers=headers, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        body = response.json()
        text_parts: list[str] = []
        for block in body.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                maybe_text = block.get("text")
                if isinstance(maybe_text, str):
                    text_parts.append(maybe_text)
        content = "\n".join(text_parts).strip() if text_parts else json.dumps(body)
        return LLMResult(
            text=content,
            model=model_spec.model,
            provider=model_spec.provider,
            latency_ms=0,
        )

    def _chat(
        self,
        model_spec: ModelSpec,
        messages: list[dict[str, str]],
        temperature: float,
        timeout_seconds: float,
    ) -> LLMResult:
        if model_spec.provider.lower() == "anthropic":
            return self._chat_anthropic(
                model_spec,
                messages=messages,
                temperature=temperature,
                timeout_seconds=timeout_seconds,
            )
        endpoint, headers = self._provider_config(model_spec.provider)
        payload = {
            "model": model_spec.model,
            "messages": messages,
            "temperature": temperature,
        }
        response = self._http.post(endpoint, headers=headers, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        body = response.json()
        choice = (body.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content")
        if not isinstance(content, str):
            content = json.dumps(body)
        usage = body.get("usage", {})
        # If provider does not report latency, approximate from token count remains unknown.
        latency_ms = int(usage.get("total_time_ms") or 0)
        return LLMResult(
            text=content,
            model=model_spec.model,
            provider=model_spec.provider,
            latency_ms=latency_ms,
        )

    def generate(
        self,
        *,
        component: str,
        phase: str,
        messages: list[dict[str, str]],
        primary: ModelSpec,
        backup: ModelSpec | None = None,
        temperature: float = 0.2,
    ) -> LLMResult:
        timeout = self.config.timeout_for(component, phase)
        try:
            return self._chat(primary, messages, temperature=temperature, timeout_seconds=timeout)
        except Exception:
            if not backup:
                raise
            retry_timeout = max(timeout * 0.9, 0.6)
            result = self._chat(
                backup,
                messages,
                temperature=temperature,
                timeout_seconds=retry_timeout,
            )
            result.fallback_used = True
            return result

    @staticmethod
    def parse_json_object(text: str) -> dict[str, Any]:
        stripped = text.strip()
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        left = stripped.find("{")
        right = stripped.rfind("}")
        if left != -1 and right != -1 and right > left:
            snippet = stripped[left : right + 1]
            try:
                parsed = json.loads(snippet)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        return {}
