from tools.email_writer import email_writer_tool
from tools.question_generator import question_generator_tool
from tools.report_writer import report_writer_tool
from tools.search_terms_generator import search_terms_generator_tool
from tools.search_executor import execute_search_plan
from schema import ReportData, ResearchContext, Question, QAItem, WebSearchPlan, ExecutedSearchPlan, EmailStatus
from agents import Agent, Runner, trace
from typing import Union


HOW_MANY_QUESTIONS = 3


MANAGER_INSTRUCTIONS = f"""
Role:
- You are the Manager Agent.

Task:
- Manage the entire research workflow from start to finish.
- Begin with exactly {HOW_MANY_QUESTIONS} clarifying Q&A turns to refine the scope.
- After the Q&A phase, delegate to generate_search_terms to create a WebSearchPlan.
- Execute the WebSearchPlan using execute_search_plan to gather summarized results.
- Transform the executed plan into a final structured report with report_writer.
- Deliver the report by email using email_writer.
- At no point should you generate questions, search terms, summaries, reports, or emails yourself; always rely on the appropriate tool.

**Ground truth context (DO NOT reconstruct it yourself):**
- RESEARCH_CONTEXT_JSON is provided below. When calling tools that require a 'context' argument, pass **exactly** this JSON string.

Operational rules:
- If Q&A turns < {HOW_MANY_QUESTIONS} → call generate_question(context=RESEARCH_CONTEXT_JSON).
- If Q&A turns == {HOW_MANY_QUESTIONS} → call generate_search_terms(context=RESEARCH_CONTEXT_JSON).
- After generate_search_terms returns a WebSearchPlan → immediately call execute_search_plan(plan).
- After execute_search_plan returns an ExecutedSearchPlan → immediately call report_writer(executed_plan=EXECUTED_PLAN, initial_query=RESEARCH_CONTEXT_JSON.initial_query).
- After report_writer returns a ReportData → immediately call email_writer(report=REPORT_DATA).
- Never modify or re-serialize RESEARCH_CONTEXT_JSON yourself; always pass it exactly as provided.

Goal:
- Ensure the process reliably produces a final cohesive research report, and that the report is successfully delivered via email to the end user.
"""


class ManagerAgent:
    def __init__(self):
        self.context = ResearchContext(initial_query="", qa_history=[])

        self.tools = [
            question_generator_tool,
            search_terms_generator_tool,
            execute_search_plan,
            report_writer_tool,
            email_writer_tool
        ]

        self.agent = Agent(
            name="Research Manager",
            instructions=MANAGER_INSTRUCTIONS,
            tools=self.tools,
            model="gpt-5",
            output_type=Union[Question, WebSearchPlan, ExecutedSearchPlan, ReportData, EmailStatus]
        )

    def reset(self):
        self.context = ResearchContext(initial_query="", qa_history=[])

    async def run(self):
        """Run the manager with the current context (does not overwrite user input)."""
        with trace("Research Manager Session"):
            result = await Runner.run(self.agent, self.context.to_input_data())

        # If the result is a Question → add a QAItem (without answer yet)
        # Handle tool outputs properly
        output = result.final_output
        if isinstance(output, Question):
            self.context.qa_history.append(QAItem(question=output))
        elif isinstance(output, EmailStatus):
            self.reset()

        return output
