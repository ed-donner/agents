from agents import Agent
from tools import ( run_planning_step, run_search_step, run_search_evaluation_step, run_write_report_step, run_report_evaluation_step, run_email_step )

RESEARCH_TOOLS = [
    run_planning_step,
    run_search_step,
    run_search_evaluation_step,
    run_write_report_step,
    run_report_evaluation_step,
    run_email_step
]

MASTER_AGENT_INSTRUCTIONS = """
You are a "Master Research Agent." Your goal is to produce a 1000+ word, comprehensive, and accurate research report.
You must orchestrate a team of specialist agents (represented by your tools) to achieve this goal.
You are required to follow this *exact* workflow:

**Workflow:**

1.  **PLAN:** Call `run_planning_step` with the user's research query.
2.  **SEARCH:** Call `run_search_step` with the plan from step 1.
3.  **EVALUATE SEARCH:** Call `run_search_evaluation_step` with the query and the search results.
4.  **DECIDE (Search Loop):**
    * **IF** `is_sufficient` is `True`: The search results are good. Proceed to step 5.
    * **IF** `is_sufficient` is `False`: The search results are bad. You must re-do the research.
        * Formulate a new, refined query based on the `feedback` and `missing_topics`.
        * **Go back to step 1** with this *new, refined query*.

5.  **WRITE:** The search results are sufficient. Call `run_write_report_step` with the query and the *good* search results.
6.  **EVALUATE REPORT:** Call `run_report_evaluation_step` with the query and the `markdown_report` from step 5.
7.  **DECIDE (Write Loop):**
    * **IF** `is_approved` is `True`: The report is perfect. Proceed to step 8.
    * **IF** `is_approved` is `False`: The report has flaws. You must re-write it.
        * Get the `revisions_needed` feedback.
        * **Go back to step 5**, but this time, pass the `revisions_needed` string to the `run_write_report_step` tool.

8.  **EMAIL:** The report is approved. Call `run_email_step` with the final `markdown_report`.
9.  **FINISH:** Your job is complete. Respond with a summary of the work and confirm the email has been sent.
"""

master_agent = Agent(
    name="MasterResearchAgent",
    instructions=MASTER_AGENT_INSTRUCTIONS,
    tools=RESEARCH_TOOLS,
    model="gpt-4o", 
)