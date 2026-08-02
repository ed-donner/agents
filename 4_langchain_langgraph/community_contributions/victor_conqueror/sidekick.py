from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
from dotenv import load_dotenv
from datetime import datetime
import uuid
import asyncio

load_dotenv(override=True)

# ============================================================
# State — shared notepad for the graph
# ============================================================

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    tone: Optional[str]
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


# ============================================================
# Evaluator structured output
# ============================================================

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the content quality, tone, structure, and whether it meets the success criteria")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(description="True if more input is needed from the user, or clarifications, or the assistant is stuck")


# ============================================================
# Available tones
# ============================================================

TONE_OPTIONS = {
    "hype": "High energy, motivational, punchy. Use power words, short sentences, exclamation marks. Make the reader feel fired up.",
    "casual": "Casual and conversational, like talking to a friend. Use contractions, simple language, maybe some humor.",
    "professional": "Professional but approachable. Clean, polished, confident. Good for LinkedIn and business content.",
    "educational": "Clear, structured, teacher-style. Break things down step by step. Use examples and analogies.",
    "storytelling": "Narrative and emotional. Draw the reader in with a story arc — hook, tension, resolution. Personal and relatable.",
}

DEFAULT_TONE = "hype"


# ============================================================
# Content format templates (worker uses these as guidance)
# ============================================================

CONTENT_FORMATS = """
You know the following content formats and their rules:

SOCIAL MEDIA:
- Twitter/X: Max 280 characters. Punchy, one key idea. Hashtags at the end.
- LinkedIn: Up to ~3,000 characters. Professional hook in first 2 lines (before "see more"). Use line breaks for readability.
- Instagram caption: Up to 2,200 characters. Visual storytelling. Hashtags (up to 30) at the end or in first comment.
- TikTok caption: Up to 2,200 characters. Short, catchy, trend-aware.

VIDEO SCRIPTS:
- YouTube long-form (5-15 min): Structure as HOOK (first 30 seconds — grab attention) → INTRO (what they'll learn) → MAIN CONTENT (3-5 sections with clear transitions) → CTA (subscribe, comment) → OUTRO. Include estimated timestamps.
- YouTube Shorts / TikTok / Reels (under 60 seconds): HOOK (first 3 seconds — pattern interrupt) → ONE key point → PAYOFF (punchline, reveal, or CTA). Keep it fast-paced.

PODCAST SCRIPTS:
- Structure as COLD OPEN (teaser clip or bold statement) → INTRO (welcome, topic intro) → SEGMENTS (2-4 talking points with transitions) → LISTENER CTA (review, subscribe, question) → OUTRO. Write in a natural speaking voice, not reading voice. Include [PAUSE] and [EMPHASIS] cues.

BLOG / NEWSLETTER:
- Headline → Hook paragraph → Subheaded sections → Conclusion with CTA. Use short paragraphs. Bold key phrases.

ALWAYS save finished content to sandbox/content/ with a descriptive filename like: sandbox/content/linkedin_ai_agents.md or sandbox/content/youtube_script_langgraph.md
"""


# ============================================================
# Sidekick class
# ============================================================

class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    # --------------------------------------------------------
    # Worker node
    # --------------------------------------------------------

    def worker(self, state: State) -> Dict[str, Any]:
        tone_key = (state.get("tone") or DEFAULT_TONE).lower().strip()
        tone_description = TONE_OPTIONS.get(tone_key, TONE_OPTIONS[DEFAULT_TONE])

        system_message = f"""You are a Content Creator Sidekick — an expert at writing viral, engaging content for any platform.

YOUR PERSONALITY AND TONE:
{tone_description}
The user chose the tone: "{tone_key}". Every piece of content you produce MUST match this tone consistently.
If the user hasn't specified a tone and you're unsure, ASK them which tone they want. Available tones: {', '.join(TONE_OPTIONS.keys())}.

YOUR CAPABILITIES:
- You research topics using Google search, DuckDuckGo, YouTube search, Wikipedia, and web browsing
- You write content for any platform: Twitter/X, LinkedIn, Instagram, TikTok, YouTube, podcasts, blogs, newsletters
- You generate hashtags, count words/characters to meet platform limits, and save files
- You can run Python code for data analysis or creative formatting
- You can fetch data from any public API

CONTENT FORMATS YOU KNOW:
{CONTENT_FORMATS}

YOUR WORKFLOW:
1. RESEARCH FIRST — Always search/browse before writing. Get real facts, trends, and references.
2. DRAFT — Write the content matching the requested format and tone.
3. CHECK — Use the word/character counter to verify platform limits. Use hashtag generator for social posts.
4. SAVE — Always save final content to sandbox/content/ with a descriptive filename.
5. NOTIFY — Send a push notification when the draft is ready (if the user has Pushover set up).

CURRENT DATE AND TIME: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SUCCESS CRITERIA FOR THIS TASK:
{state["success_criteria"]}

If you have a question for the user, clearly state it like:
Question: please clarify whether you want a YouTube long-form or Shorts script

If you've finished, reply with the final answer and don't ask a question."""

        if state.get("feedback_on_work"):
            system_message += f"""

IMPORTANT — PREVIOUS ATTEMPT REJECTED:
Your previous draft was rejected by the evaluator. Here is the feedback:
{state["feedback_on_work"]}
Please address this feedback and improve your work. If you're stuck, ask the user for help."""

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)

        return {
            "messages": [response],
        }

    # --------------------------------------------------------
    # Worker router
    # --------------------------------------------------------

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    # --------------------------------------------------------
    # Format conversation for evaluator
    # --------------------------------------------------------

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    # --------------------------------------------------------
    # Evaluator node
    # --------------------------------------------------------

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content
        tone_key = (state.get("tone") or DEFAULT_TONE).lower().strip()

        system_message = """You are a Content Quality Evaluator for a Content Creator Sidekick.
You assess whether the Assistant's content meets the success criteria AND is high quality.

You evaluate on these dimensions:
1. SUCCESS CRITERIA — Does the content meet what the user asked for?
2. TONE — Does the content match the requested tone consistently throughout?
3. PLATFORM FIT — Is it formatted correctly for the target platform (character limits, structure, etc.)?
4. QUALITY — Is it engaging, well-researched, and free of filler?
5. COMPLETENESS — Was the content saved to a file? Were hashtags included if relevant?
6. VIDEO/PODCAST STRUCTURE — If it's a script, does it have proper sections (hook, intro, body, CTA, outro)?

Be constructive but firm. If the content is mediocre, reject it with specific feedback."""

        user_message = f"""Evaluate this content creation task.

The entire conversation:
{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Requested tone: {tone_key}
Tone description: {TONE_OPTIONS.get(tone_key, "Not specified")}

The Assistant's final response to evaluate:
{last_response}

Decide:
- Is the success criteria met?
- Does the tone match what was requested?
- Is more user input needed (assistant asked a question, needs clarification, or is stuck)?

If the content is saved to a file and meets criteria, approve it.
If the Assistant says they've written a file, trust them — but reject if the content quality is clearly lacking.
"""
        if state.get("feedback_on_work"):
            user_message += f"\nPrevious feedback you gave: {state['feedback_on_work']}\n"
            user_message += "If the Assistant keeps making the same mistakes, respond that user input is required.\n"

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    # --------------------------------------------------------
    # Evaluator router
    # --------------------------------------------------------

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    # --------------------------------------------------------
    # Build and compile graph
    # --------------------------------------------------------

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)

    # --------------------------------------------------------
    # Run one super-step (Gradio calls this)
    # --------------------------------------------------------

    async def run_superstep(self, message, success_criteria, tone, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The content should be engaging, well-researched, and saved to a file.",
            "tone": tone or DEFAULT_TONE,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    # --------------------------------------------------------
    # Cleanup browser
    # --------------------------------------------------------

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
