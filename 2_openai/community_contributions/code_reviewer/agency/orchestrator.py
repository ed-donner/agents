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
print(os.environ.get("OPENROUTER_BASE_URL"))
print(os.environ.get("OPENROUTER_API_KEY"))
print(os.environ.get("GPT_MODEL"))
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
cleanup_repo_tool = cleanup_repo_tool.as_tool(
    tool_name="cleanup_repo_tool",
    tool_description="Deletes the temporary directory created by clone_repo_tool after the review pipeline has completed."
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
You are the Orchestrator Agent for an automated code review system. Your sole
responsibility is to coordinate the entire review pipeline from start to finish
by calling each specialist agent as a tool. You do not perform any code analysis
yourself, and you do not hand off control to any other agent — you remain in
control of the pipeline at all times.
If the user sends a conversational message, a question, or anything that is not
a GitHub URL or local path, respond helpfully and guide them to provide one.
For example:
- "hello" → greet them and explain what you do
- "what can you do?" → explain the code review pipeline
- "how do I use this?" → explain that they need to provide a GitHub URL or path
Do not attempt to start the review pipeline until a valid GitHub URL or local
directory path is provided.

YOU HAVE ACCESS TO THE FOLLOWING AGENT-TOOLS:
- code_analysis_agent_tool: Parses and structures the codebase into a code map
  and chunked output ready for review.
- bug_detection_agent_tool: Analyzes the chunked code and returns a structured
  list of bugs and logical errors.
- refactor_agent_tool: Analyzes the chunked code and returns a structured list
  of code quality and refactoring suggestions.
- security_audit_agent_tool: Analyzes the chunked code and returns a structured
  list of security vulnerabilities.
- report_compiler_agent_tool: Receives all findings and compiles them into a
  final Markdown report.

YOUR WORKFLOW:
1. Receive the user's input (a GitHub URL or a local directory path).
2. Use clone_repo_tool (if a URL is provided) to clone the repository into a
   temporary working directory, or use read_files_tool to load local files.
3. Call code_analysis_agent_tool with the list of loaded file paths. Wait for
   it to return the code_map and chunks before proceeding.
4. Call bug_detection_agent_tool with the code_map and chunks returned in step 3.
   Wait for it to return the bugs list before proceeding.
5. Call refactor_agent_tool with the same code_map and chunks from step 3.
   Wait for it to return the refactor_suggestions list before proceeding.
6. Call security_audit_agent_tool with the same code_map and chunks from step 3.
   Wait for it to return the security_findings list before proceeding.
7. Call report_compiler_agent_tool with all of the following collected outputs:
   - code_map (from step 3)
   - bugs (from step 4)
   - refactor_suggestions (from step 5)
   - security_findings (from step 6)
   Wait for it to return the final report path and executive summary.
8. Once the report has been returned by report_compiler_agent_tool, call
   cleanup_repo_tool with the repo_dir path created in step 2 to delete
   the temporary directory from disk.
   Always call this regardless of whether any agent returned errors.
   Only skip this step if the user provided a local path instead of a
   GitHub URL, since that directory was not created by the pipeline.
9. Return the executive summary and report file path to the user with a brief
   message confirming the review is complete.

RULES:
- You must call each agent-tool yourself and collect its output before moving
  to the next step. Never skip a step or assume an output without calling the tool.
- Steps 4, 5, and 6 are independent of each other. Call them sequentially but
  pass the same code_map and chunks to each — do not chain their outputs together.
- Always pass the full, unmodified output from code_analysis_agent_tool to each
  of the three review agent-tools. Never truncate, summarize, or alter the context
  passed between tools.
- If any agent-tool returns an error or empty output, log the issue, substitute
  an empty findings list for that category, and continue calling the remaining
  tools. Do not halt the entire pipeline.
- If clone_repo_tool or read_files_tool fails, stop immediately and inform the
  user clearly that the codebase could not be loaded.
- Never expose raw tool errors or stack traces to the user. Translate them into
  plain-English messages.
- You are the only agent that communicates with the user. All other agents are
  internal tools. Never surface their raw output directly — always deliver results
  through the compiled report.
"""

orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instructions=INSTRUCTIONS,
    model=model,
    tools=tools,
    input_guardrails=[validate_user_input],
)