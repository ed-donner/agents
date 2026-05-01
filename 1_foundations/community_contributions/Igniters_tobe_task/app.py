"""
Bio Agent — Gradio Entrypoint
-------------------------------
Minimal UI layer. All logic lives in agent.py.
"""

import gradio as gr
from agent import BioAgent


def main():
    agent = BioAgent()

    demo = gr.ChatInterface(
        fn=agent.chat,
        type="messages",
        title="🤖 Bio Agent — Career Assistant",
        description=(
            "Ask me anything about my professional background, "
            "skills, experience, or projects. I'm powered by a local LLM "
            "with RAG and self-evaluation."
        ),
        examples=[
            "What are your core technical strengths?",
            "Tell me about your engineering mindset.",
            "What kind of AI systems have you built?",
            "What's your approach to problem-solving?",
        ],
    )

    demo.launch()


if __name__ == "__main__":
    main()
