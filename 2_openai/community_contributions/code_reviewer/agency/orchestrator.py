import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from .code_analysis import code_analysis_agent
from .bug_detection import bug_detection_agent
from .refactor_suggestion import refactor_suggestion_agent
from .security_audit import security_audit_agent
from .report_compiler import report_compiler_agent
from tools import clone_repo_tool, cleanup_repo_tool
from guardrails import validate_user_input

load_dotenv(override=True)

client = AsyncOpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL"), api_key=os.environ.get("OPENROUTER_API_KEY"))
model = OpenAIChatCompletionsModel(model=os.environ.get("GPT_MODEL"), openai_client=client)

code_analysis_agent_tool = code_analysis_agent.as_tool(
    tool_name="code_analysis_agent_tool",
    tool_description="Parses and structures the codebase into a code map and chunks."
)
bug_detection_agent_tool = bug_detection_agent.as_tool(
    tool_name="bug_detection_agent_tool",
    tool_description="Analyzes code chunks and returns a list of bugs and logical errors."
)
refactor_agent_tool = refactor_suggestion_agent.as_tool(
    tool_name="refactor_agent_tool",
    tool_description="Analyzes code chunks and returns code quality improvement suggestions."
)
security_audit_agent_tool = security_audit_agent.as_tool(
    tool_name="security_audit_agent_tool",
    tool_description="Analyzes code chunks and returns a list of security vulnerabilities."
)
report_compiler_agent_tool = report_compiler_agent.as_tool(
    tool_name="report_compiler_agent_tool",
    tool_description="Compiles all findings into a final Markdown report."
)

tools = [
    clone_repo_tool,
    cleanup_repo_tool,
    code_analysis_agent_tool,
    bug_detection_agent_tool,
    refactor_agent_tool,    
    security_audit_agent_tool,
    report_compiler_agent_tool,
]


INSTRUCTIONS = """
You coordinate the code review pipeline by calling specialist agents as tools.
You do not analyze code yourself.

1. If input is conversational, respond helpfully and ask for a GitHub URL or
   local path before proceeding.
2. Clone (clone_repo_tool) or read (read_files_tool) the codebase. Stop if
   either fails.
3. Call code_analysis_agent_tool with the file paths. Collect code_map and chunks.
4. Call bug_detection_agent_tool, refactor_agent_tool, and
   security_audit_agent_tool with the same code_map and chunks.
5. Call report_compiler_agent_tool with code_map, bugs, refactor_suggestions,
   and security_findings.
6. Call cleanup_repo_tool if a repo was cloned in step 2.
7. Return the executive summary and report path to the user.

- Substitute an empty findings list for any agent that errors. Never halt.
- Never expose raw errors to the user.
- Only you communicate with the user."""

orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instructions=INSTRUCTIONS,
    model=model,
    tools=tools,
    input_guardrails=[validate_user_input],
)