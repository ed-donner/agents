from agents import Agent, Runner, function_tool, ModelSettings
from pydantic import BaseModel, Field

INSTRUCTIONS = """You are a research scoping assistant. Analyze the user's research query and decide
how many clarifying questions (0 to 5) are needed before proceeding.

Ambiguity guidelines:
- 0 questions: query is specific, clear, and well-scoped (e.g. "latest AI chip benchmarks 2025")
- 1-2 questions: mostly clear but missing one or two important details
- 3-4 questions: broad topic that needs meaningful scoping
- 5 questions: highly ambiguous or covers many possible interpretations

Question design rules:
- Every question MUST have 2-4 predefined answer options the user can select
- For yes/no questions use options: ["Yes", "No"]
- For categorical questions provide 2-4 specific, mutually exclusive options relevant to that query
  (e.g. ["Academic / research", "Business / professional", "Personal learning"] for audience)
- Do NOT include "Other" in options — it is added to every question automatically
- Keep question text concise (one sentence)
- Cover different dimensions: audience, time range, geography, depth, use case, format — not the same dimension twice

You MUST call `submit_questions` exactly once.
Pass an empty list [] if no clarification is needed.
"""


class ClarifyingQuestion(BaseModel):
    question: str = Field(description="The clarifying question (one sentence).")
    options: list[str] = Field(
        description=(
            "2-4 predefined answer options the user can select. "
            "For yes/no questions use ['Yes', 'No']. "
            "For categorical questions provide specific, mutually exclusive options. "
            "Do NOT include 'Other' — it is added automatically."
        )
    )


class ClarifierAgent:
    """Agentic clarifier that autonomously decides how many structured questions to ask (0-5)."""

    async def run(self, query: str) -> list[dict]:
        """Return a list of 0–5 questions, each with predefined answer options."""
        captured: list[dict] = []

        @function_tool
        def submit_questions(questions: list[ClarifyingQuestion]) -> str:
            """Submit 0-5 clarifying questions. Each question must have predefined answer options.
            Call with an empty list [] if the query is already specific and clear."""
            for q in questions[:5]:
                captured.append({"question": q.question, "options": q.options})
            return f"Submitted {len(captured)} question(s)."

        agent = Agent(
            name="ClarifierAgent",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            tools=[submit_questions],
            model_settings=ModelSettings(tool_choice="required"),
        )

        await Runner.run(agent, f"Research query: {query}")
        return captured
