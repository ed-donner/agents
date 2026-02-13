"""
Intake Agent - handles the initial user interaction phase.

This agent:
1. Takes the raw topic and generates 3 clarifying questions
2. Takes the user's answers and produces a locked ResearchBrief

The brief cannot be modified once research begins.
"""

from agents import Agent, AgentOutputSchema
from models import FollowUpQuestions, ResearchBrief


# Agent for generating follow-up questions
QUESTIONS_INSTRUCTIONS = """You are a research intake specialist. Your job is to ask clarifying questions
before research begins to ensure the final report meets the user's actual needs.

Given a research topic, generate exactly 3 follow-up questions that will help scope the research:

1. **Intended use**: What will this research be used for? (e.g., internal decision, client presentation, blog post)
2. **Scope constraints**: Any boundaries on time period, geographic region, depth, or sources to exclude?
3. **Desired angle**: Should the report focus on opportunities/best-case, risks/concerns, or a balanced view?

Keep questions concise and practical. Don't ask obvious questions - focus on what genuinely affects research direction.
"""

questions_agent = Agent(
    name="IntakeQuestionsAgent",
    instructions=QUESTIONS_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=AgentOutputSchema(FollowUpQuestions, strict_json_schema=True),
)


# Agent for producing the locked research brief
BRIEF_INSTRUCTIONS = """You are a research intake specialist. Synthesize the user's topic and answers into a research brief.

You will receive:
1. The original research topic
2. Three clarifying questions and the user's answers

Output a ResearchBrief with these exact fields:
- topic: The core research question (string)
- intended_use: How the research will be used (string)
- scope_constraints: Any boundaries on scope, time, region, etc. (string)
- desired_angle: Must be exactly one of: "best_case", "risks", or "balanced"
- follow_up_answers: A dict mapping each question to its answer

Be concise and precise.
"""

brief_agent = Agent(
    name="IntakeBriefAgent",
    instructions=BRIEF_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=AgentOutputSchema(ResearchBrief, strict_json_schema=False),
)
