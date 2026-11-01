from planner_agent import planner_agent
from search_agent import search_agent
from clarification_agent import clarification_agent, register_back_handoff
from writer_agent import writer_agent
from agents import Agent, handoff
from dotenv import load_dotenv
import os

load_dotenv(override=True)
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")

description1 = (
    "Clarify and refine an ambiguous research query BEFORE planning searches. "
    "Hand off to the clarification agent whenever the query is unclear, too broad, or you would need "
    "more information from the user. Use this handoff instead of answering with a question of your own. "
    "The clarification agent either asks the user a question (ClarificationData) or hands control back "
    "to you (return_to_manager) when the query is already clear. Do NOT plan or search until the query is clear."
)
description2 = (
    "Break a clarified query into a list of web searches to run. "
    "Input: the clarified/refined query string. "
    "Returns a search plan containing a `searches` list, where each item has `query` (the search term) and "
    "`reason` (why it matters). Use this ONCE per research task, then run the search tool for each item."
)
description3 = (
    "Run ONE web search and get a concise summary of the results. "
    "Input: a single search term (one item's `query` from the search plan). "
    "Returns a 2-3 paragraph summary (<300 words) of what was found. "
    "Call this tool once per search item from the plan, in a loop, and collect all summaries."
)
description4 = (
    "Write the final, readable report from the gathered research. "
    "Input: the ORIGINAL user query plus ALL the collected search summaries (and their sources). "
    "Returns an object with `short_summary` (2-3 sentences), `markdown_report` (the full, detailed report), "
    "and `follow_up_questions` (suggested further topics). Call this ONCE at the very end."
)

# The clarification step is a HANDOFF (control moves to the clarification agent),
# not a tool: this way Runner.run() ends on the clarification agent and its
# final_output is a ClarificationData object we can inspect from the outside.
handoff1 = handoff(
    clarification_agent,
    tool_name_override="clarify_query",
    tool_description_override=description1,
)
tool1 = planner_agent.as_tool(tool_name="plan_searches", tool_description=description2)
tool2 = search_agent.as_tool(tool_name="search_agent", tool_description=description3)
tool3 = writer_agent.as_tool(tool_name="writer_agent", tool_description=description4)

tools = [tool1, tool2, tool3]

INSTRUCTIONS = f"""
You are the research orchestrator. You coordinate the research pipeline:
clarification -> search planning -> searching -> report writing.

HARD RULE (read this first):
- You may ONLY return a final report to the user AFTER the query is fully clear AND the PLAN, SEARCH
  and WRITE stages are all complete.
- If the query is not clear enough, or you still need ANY information from the user, you MUST NOT answer
  the user with text, and you MUST NOT ask the user a question yourself. Your ONLY allowed action is to
  hand off to the clarification agent (`clarify_query`). Asking a question or requesting more information
  in plain text is FORBIDDEN - always route it through the handoff.

Follow these stages IN ORDER:

1. CLARIFY (clarify_query is a HANDOFF, not a tool)
   - If the user's query is NOT clearly and specifically understood, hand off to the clarification agent
     (call the `clarify_query` handoff).
   - When you hand off, CONTROL MOVES to the clarification agent. It will EITHER:
       (a) ask the user one question with a few options and end the turn with a ClarificationData
           object ({{"query", "question", "options"}}) so the user can answer, OR
       (b) hand control BACK to you via `return_to_manager` when the query is already clear enough.
   - If the clarification agent hands back to you (return_to_manager), its note will say the query is
     clear and that NO more questions are needed. When that happens you MUST accept that verdict:
     do NOT hand off to clarification again and do NOT ask anything - go straight to PLAN below.
   - If the user answers a clarification question and you still truly need more information, you may
     hand off to the clarification agent again.
   - Never plan or search while the query is still unclear.
   - Never end a turn with a question or a request for more information in plain text -
     that is exactly what the handoff is for.

2. PLAN (plan_searches)
   - Once the query is clear, call the plan tool ONCE with the refined query.
   - It returns a `searches` list; each item has a `query` (search term) and a `reason`.

3. SEARCH (search_agent)
   - The search tool is the ONLY tool you call multiple times. For EACH search item in the plan,
     call the search tool ONCE, passing only that item's search term. When possible, issue these
     calls in parallel.
   - Continue until every search item has been executed. Collect and remember every summary,
     keeping track of which summary belongs to which search term/reason.
   - Do not skip items and do not stop early.

4. WRITE (writer_agent)
   - After ALL searches are done, call the writer tool ONCE. Pass the ORIGINAL user query together with
     ALL the collected search summaries (include the search terms/sources so the report can cite them).
   - Use the writer's `markdown_report` as the final answer.

Rules:
- UNLESS the query is clear, your ONLY valid response is the `clarify_query` handoff. Do not reply to the
  user with a question, a clarification request, or a partial answer in plain text.
- If a clarification round returns `return_to_manager` saying the query is clear, respect it: proceed to
  PLAN immediately and do NOT hand off to clarification again.
- Clarification is a handoff: use it while the query still needs clarification, and stop after
  handing off so the user can answer.
- The search tool is the only tool that runs several times; the plan and writer tools are called exactly
  once per research task.
- Never call the writer tool before all searches have completed.
- Never produce a final report unless PLAN, SEARCH and WRITE have all actually run.
- Base the final report only on the collected search results; do not fabricate facts.
- Keep the user informed of which stage you are in, briefly.
"""


manager_agent = Agent(
    name="Search_Manager",
    instructions=INSTRUCTIONS,
    tools=tools,
    handoffs=[handoff1],  # the clarify_query handoff (kept separate from tools)
    model=MODEL_NAME,
)

# Register the back-handoff (clarification -> manager) AFTER manager_agent exists,
# to avoid a circular import in clarification_agent.
register_back_handoff(manager_agent)
