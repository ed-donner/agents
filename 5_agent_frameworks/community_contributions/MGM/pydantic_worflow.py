import asyncio
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pydantic_graph import GraphBuilder, StepContext
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from fastmcp.client.transports import StdioTransport

load_dotenv(override=True)

# -------------------------------------------------------------------
# Workspace & Tool Setup
workspace = os.path.abspath("workspace")
os.makedirs(workspace, exist_ok=True)

filesystem_toolset = MCPToolset(
    StdioTransport(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", workspace],
        cwd=workspace,
    )
)

# -------------------------------------------------------------------
# MODEL CLIENT (OLLAMA TARGET)
# Ollama exposes an OpenAI-compatible endpoint, so we reuse OpenAIChatModel
# with a custom base_url, same idea as agent_framework's OpenAIChatCompletionClient.
ollama_model = OpenAIChatModel(
    "qwen2.5:7b",
    provider=OpenAIProvider(
        base_url=os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1"),
        api_key="ollama",
    ),
)

# -------------------------------------------------------------------
# WORKER AGENTS
writer_agent = Agent(
    ollama_model,
    instructions="You are a professional creative marketer. Write a concise, 1-sentence product tagline. Do not use quotation marks.",
    name="WriterAgent",
)

# Only the translator needs filesystem access in this workflow (matches the
# original: the FileSaver step is the one that writes to disk), but nothing
# stops you from attaching the toolset to any/all agents that need it.
translator_agent = Agent(
    ollama_model,
    instructions="You are an expert translator. Translate the given text exactly into natural Spanish. Return only the final Spanish text.",
    name="TranslatorAgent",
)

# -------------------------------------------------------------------
# GRAPH STATE
# Unlike agent_framework's State (pending/commit buffer, .get()/.set() only),
# pydantic_graph's state is just a plain dataclass instance you mutate directly
# via ctx.state.<field> = value. It's passed into graph.run(state=...) and
# threaded through every step automatically.
@dataclass
class WorkflowState:
    saved_text: str = ""

# -------------------------------------------------------------------
# BUILD THE GRAPH
g = GraphBuilder(state_type=WorkflowState, output_type=str)

@g.step
async def write_tagline(ctx: StepContext[WorkflowState, None, str]) -> str:
    """
    Invokes the writer agent to generate a marketing tagline based on the input text.

    Args:
        ctx: The step context containing the input prompt string from the previous step.

    Returns:
        str: The generated tagline output from the writer agent.
    """
    print("\n🚀 [AGENT INITIALIZED] Running writer agent...")
    print(f"📥 [LATEST INPUT]: {ctx.inputs}")
    result = await writer_agent.run(ctx.inputs)
    print(f"📤 [AGENT RESPONSE]: {result.output}")
    return result.output


@g.step
async def translate(ctx: StepContext[WorkflowState, None, str]) -> str:
    """
    Invokes the translator agent to translate the provided text into the target language.
    
    If the agent returns an empty response, a default organic energy drink tagline in Spanish is 
    applied as a fallback.

    Args:
        ctx: The step context containing the text string to be translated.

    Returns:
        str: The translated text, or the default fallback tagline if empty.
    """
    print("\n🚀 [AGENT INITIALIZED] Running translator agent...")
    print(f"📥 [LATEST INPUT]: {ctx.inputs}")
    result = await translator_agent.run(ctx.inputs)
    text = result.output.strip() or "Una bebida energética orgánica de alto rendimiento para programadores."
    print(f"📤 [AGENT RESPONSE]: {text}")
    return text


@g.step
async def ask_human(ctx: StepContext[WorkflowState, None, str]) -> str:
    """
    Displays a translation preview to the user and blocks until they provide
    console input confirming whether they want to save the output.
    
    Also stashes the current input into the global graph state.
    """
    ctx.state.saved_text = ctx.inputs

    print(f"\n🔍 [TRANSLATION PREVIEW]:\n{ctx.inputs}")
    choice = input("💾 Would you like to save this translation to a file? (y/n): ").strip().lower()
    return choice


@g.step
async def save_file(ctx: StepContext[WorkflowState, None, str]) -> str:
    """
    Persists the stashed text from the workflow state to a file.
    
    Attempts to use the Model Context Protocol (MCP) Filesystem toolset first. 
    If the MCP tool call fails, it falls back to standard synchronous local 
    file system operations.

    Args:
        ctx: The step context containing the global graph state.

    Returns:
        str: The raw text that was saved to disk.
    """
    text_to_save = ctx.state.saved_text
    print("\n🔧 [WORKFLOW INTEROP] Handing file operation over to MCP Filesystem...")

    try:
        async with filesystem_toolset:
            await filesystem_toolset.direct_call_tool(
                "write_file", {"path": "pydabtic_translate.txt", "content": text_to_save}
            )
        print("✨ SUCCESS: MCP tool written to pydabtic_translate.txt.")
    except Exception as e:
        print(f"⚠️ Direct MCP call failed ({e}). Falling back to manual write...")
        file_path = os.path.join(workspace, "pydabtic_translate.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_to_save)
        print(f"✨ Fallback SUCCESS: File created at {file_path}")

    return text_to_save


@g.step
async def format_output(ctx: StepContext[WorkflowState, None, str]) -> str:
    """
    Formats the workflow text into a standardized uppercase brand presentation string.
    
    Prioritizes text incoming from the immediate previous step (`ctx.inputs`). 
    If no input is present, it falls back to reading the stashed text directly 
    from the global graph state (`ctx.state.saved_text`).

    Args:
        ctx: The step context containing the incoming string or graph state.

    Returns:
        str: The final stylized and capitalized text string.
    """
    text_to_format = ctx.inputs if ctx.inputs else ctx.state.saved_text
    return f"*** BRAND OUTPUT ***\n{text_to_format.upper()}"


g.add(
    g.edge_from(g.start_node).to(write_tagline),
    g.edge_from(write_tagline).to(translate),
    g.edge_from(translate).to(ask_human),

    # Conditional branch: ask_human returns "y"/"n" and the decision node
    # routes accordingly - the direct equivalent of should_save/should_skip
    # conditions on WorkflowBuilder.add_edge in agent_framework.
    g.edge_from(ask_human).to(
        g.decision()
        .branch(g.match(str, matches=lambda choice: choice in ("y", "yes")).to(save_file))
        .branch(g.match(str, matches=lambda choice: choice not in ("y", "yes")).to(format_output))
    ),

    g.edge_from(save_file).to(format_output),
    g.edge_from(format_output).to(g.end_node),
)

workflow = g.build()

# -------------------------------------------------------------------
# RUN THE WORKFLOW
async def main():
    print("🎬 Starting multi-agent Ollama Workflow (Pydantic AI)...")

    result = await workflow.run(
        state=WorkflowState(),
        inputs="A high-performance organic energy drink for programmers.",
    )

    print("\n🏁 [WORKFLOW EXECUTION COMPLETE]")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())