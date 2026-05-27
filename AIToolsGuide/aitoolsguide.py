import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

__author__ = "Zubair Khan"


class AIToolsGuide:
    """Simple wrapper for Groq-backed chat completions. This will provide answers to th queries about differnt AI tools"""

    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        model_name: str = "openai/gpt-oss-120b",
        prompt_path: Optional[str] = None,
    ) -> None:
        """Initialize API client, model name, and system prompt."""
        load_dotenv(override=True)

        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Set it in your environment or pass groq_api_key explicitly."
            )

        self.model_name = model_name
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.system_prompt = self._load_prompt(prompt_path)

    def _load_prompt(self, prompt_path: Optional[str]) -> str:
        """Load the system prompt text from a markdown file."""
        path = Path(prompt_path) if prompt_path else Path(__file__).with_name("prompt.md")
        if not path.is_file():
            raise FileNotFoundError(f"System prompt file not found at '{path}'.")
        return path.read_text(encoding="utf-8")

    def chat(
        self,
        message: str,
        history: Optional[list[dict]] = None,
    ) -> str:
        """Generate an assistant response using optional chat history."""
        history = history or []
        clean_history = [
            {"role": str(msg["role"]), "content": str(msg["content"])}
            for msg in history
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]
        messages = [
            {"role": "system", "content": self.system_prompt},
            *clean_history,
            {"role": "user", "content": str(message)},
        ]

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        return response.choices[0].message.content or ""


def create_gradio_interface():
    """
    Build and return a reusable Gradio chat interface.
    """
    import gradio as gr

    guide = AIToolsGuide()

    def _chat(message, history):
        """Normalize Gradio inputs and return the assistant reply."""
        converted_history: list[dict[str, str]] = []

        # Gradio can provide history in multiple formats depending on `type=...`.
        # Support both:
        # - type="messages": history is a list[{"role": ..., "content": ...}, ...]
        # - default: history is a list[(user, assistant), ...]
        if isinstance(history, list) and history:
            first = history[0]
            if isinstance(first, dict) and "role" in first and "content" in first:
                for msg in history:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        converted_history.append(
                            {"role": str(msg["role"]), "content": str(msg["content"])}
                        )
            else:
                for item in history:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        user_msg, assistant_msg = item[0], item[1]
                        if user_msg:
                            converted_history.append({"role": "user", "content": str(user_msg)})
                        if assistant_msg:
                            converted_history.append(
                                {"role": "assistant", "content": str(assistant_msg)}
                            )

        # With type="messages", `message` is usually a dict like {"role":"user","content":"..."}.
        if isinstance(message, dict) and "content" in message:
            user_text = str(message["content"])
        else:
            user_text = str(message)

        reply = guide.chat(user_text, converted_history)
        return reply

    return gr.ChatInterface(_chat, type="messages")


if __name__ == "__main__":
    # Launch a Gradio interface when run as a script.
    iface = create_gradio_interface()
    iface.launch()

