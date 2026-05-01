import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from tools import parse_code_tool, chunk_code_tool, read_files_tool
from models import CodeAnalysisOutput

load_dotenv(override=True)

client = AsyncOpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL"), api_key=os.environ.get("OPENROUTER_API_KEY"))
model = OpenAIChatCompletionsModel(model=os.environ.get("CLAUDE_MODEL"), openai_client=client)

tools = [
    read_files_tool,
    parse_code_tool,
    chunk_code_tool,
]

INSTRUCTIONS = """
You parse and structure the codebase for downstream agents.

1. Call read_files_tool to load all supported source files.
2. Call parse_code_tool on each file to extract classes, functions,
   imports, and line count. Flag unparseable files and skip them.
3. Call chunk_code_tool on any file exceeding 300 lines.
4. Return code_map and chunks to the Orchestrator.

- Do not assess code quality, bugs, or security.
- Preserve all source code exactly as-is."""

code_analysis_agent = Agent(
    name="Code Analysis Agent",
    instructions=INSTRUCTIONS,
    output_type=CodeAnalysisOutput,
    model=model,
    tools=tools,
)