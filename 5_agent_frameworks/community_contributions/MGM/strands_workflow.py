import re
import asyncio
import os
from typing import Any
from dotenv import load_dotenv
from mcp.client.stdio import stdio_client, StdioServerParameters
from strands import Agent
from strands.agent.agent_result import AgentResult
from strands.models.openai import OpenAIModel
from strands.multiagent import GraphBuilder
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, NodeResult
from strands.multiagent.graph import GraphState
from strands.telemetry.metrics import EventLoopMetrics
from strands.tools.mcp import MCPClient

# Load environment configuration variables
load_dotenv(override=True)

# -------------------------------------------------------------------
# Establish target workspace directory structure for file generation
workspace = os.path.abspath("workspace")
os.makedirs(workspace, exist_ok=True)

# Instantiate the Model Context Protocol (MCP) Filesystem server client
filesystem_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", workspace],
            cwd=workspace
        )
    )
)

# -------------------------------------------------------------------
# Configure the local inference server endpoint client mapping to Ollama
ollama_model = OpenAIModel(
    client_args={
        "api_key": "Ollama",
        "base_url": "http://localhost:11434/v1"
    },
    model_id="qwen2.5:7b",
    params={
        "temperature": 0.1,
        "seed": 42,
        "tool_choice": "auto",    # explicit, though it's the default
    },
)

# -------------------------------------------------------------------
# Agent configurations
# Marketing specialist tasked with generation of product copy
writer_agent = Agent(
    model=ollama_model,
    name="WriterAgent",
    system_prompt="You are a professional creative marketer. Write a concise, 1-sentence product tagline. Do not use quotation marks.",
)

# Language translation engine translating input into target format
translator_agent = Agent(
    model=ollama_model,
    name="TranslatorAgent",
    system_prompt="You are an expert translator. Translate the given text exactly into natural Spanish. Return only the final Spanish text.",
)


def _make_agent_result(text: str) -> AgentResult:
    """
    Builds a minimal AgentResult wrapping the provided raw string payload.
    
    This ensures functional node outputs match agent signatures, making them 
    compatible with the graph execution engine's downstream evaluations.
    """
    return AgentResult(
        stop_reason="end_turn",
        message={"role": "assistant", "content": [{"text": text}]},
        metrics=EventLoopMetrics(),
        state={},
    )


def _extract_text(task: Any) -> str:
    """
    Extracts and standardizes data payloads into a plain string.
    
    Handles initial entry inputs (raw string) as well as intermediary content 
    blocks built dynamically by upstream graph nodes (list of dictionaries).
    """
    if isinstance(task, str):
        return task
    if isinstance(task, list):
        return "\n".join(block["text"] for block in task if isinstance(block, dict) and "text" in block)
    return str(task)


def _node_text(state: GraphState, node_id: str) -> str:
    """
    Extracts and flattens text contents generated from a target node execution.
    
    Accesses the completed node inside the active GraphState context and flattens 
    either an AgentResult or multi-agent layout down into an evaluation string.
    """
    node_result = state.results.get(node_id)
    if node_result is None:
        return ""
    return "\n".join(str(r) for r in node_result.get_agent_results()).strip()


class FunctionNode(MultiAgentBase):
    """
    Adapter wrapper converting standard functions into valid MultiAgentBase nodes.
    
    Enables arbitrary, deterministic execution branches to be registered inside 
    the GraphBuilder without creating fully managed AI Agent objects.
    It is the same role our Executor subclasses played in agent_framework.
    
    Note: As of this SDK version, GraphBuilder.add_node() only accepts AgentBase or 
    MultiAgentBase instances - plain functions aren't supported as first-class nodes 
    yet (tracked upstream in strands-agents/sdk-python#544). 
    """
    def __init__(self, fn, node_id: str):
        self.id = node_id
        self._fn = fn

    async def invoke_async(self, task: Any, invocation_state: dict | None = None, **kwargs: Any) -> MultiAgentResult:
        """
        Executes the underlying functional callable within the graph pipeline loop.
        """
        text_in = _extract_text(task)
        state = invocation_state if invocation_state is not None else {}
        if asyncio.iscoroutinefunction(self._fn):
            output_text = await self._fn(text_in, state)
        else:
            output_text = self._fn(text_in, state)
        return MultiAgentResult(results={self.id: NodeResult(result=_make_agent_result(output_text))})


def ask_human(text: str, invocation_state: dict) -> str:
    """
    Prompts human operator via console input to decide if progress is persisted.
    
    Stashes the validated string content inside the shared `invocation_state` 
    reference mapping so it can be extracted in later pipeline steps.
    """
    print(f"\n🔍 [TRANSLATION PREVIEW]:\n{text}")
    invocation_state["saved_text"] = text
    answer = input("💾 Would you like to save this translation to a file? (y/n): ").strip().lower()
    print(f"🔍 DEBUG: received answer = {answer!r}")   # <-- add this
    return answer


def _extract_last_agent_response(text: str) -> str:
    """
    Strips the graph-generated lineage wrapper ('Original Task: ...',
    'Inputs from previous nodes: ...') and returns only the most recent
    upstream agent's raw output.
    """
    matches = re.findall(r"-\s*Agent:\s*(.+)", text)
    if matches:
        return matches[-1].strip()
    return text.strip()


def ask_human(text: str, invocation_state: dict) -> str:
    """
    Prompts human operator via console input to decide if progress is persisted.
    
    Stashes the validated string content inside the shared `invocation_state` 
    reference mapping so it can be extracted in later pipeline steps.
    """
    print(f"\n🔍 [TRANSLATION PREVIEW]:\n{text}")
    clean_text = _extract_last_agent_response(text)
    invocation_state["saved_text"] = clean_text
    answer = input("💾 Would you like to save this translation to a file? (y/n): ").strip().lower()
    print(f"🔍 DEBUG: received answer = {answer!r}")
    return answer

def save_file(_text: str, invocation_state: dict) -> str:
    """
    Saves stashed string content to disk using the active workspace directory.
    
    Attempts to issue write calls via MCP Client server tools first. If an 
    error or interface exception surfaces, falls back to native filesystem operations.
    """
    text_to_save = invocation_state.get("saved_text", "")
    print("\n🔧 [WORKFLOW INTEROP] Handing file operation over to MCP Filesystem...")

    try:
        with filesystem_mcp:
            result = filesystem_mcp.call_tool_sync(
                tool_use_id="save-translation",
                name="write_file",
                arguments={"path": "strands_translate.txt", "content": text_to_save},
            )
        if getattr(result, "isError", False):
            raise RuntimeError(f"MCP tool reported error: {result}")
        print("✨ SUCCESS: MCP tool written to strands_translate.txt.")
        print(f"🔍 DEBUG: MCP result = {result!r}")
    except Exception as e:
        print(f"⚠️ Direct MCP call failed ({e}). Falling back to manual write...")
        file_path = os.path.join(workspace, "strands_translate.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_to_save)
        print(f"✨ Fallback SUCCESS: File created at {file_path}")

    return text_to_save


def format_output(_text: str, invocation_state: dict) -> str:
    """
    Fetches the stashed data state and constructs a stylized marketing block.
    
    Transforms values into an uppercase format prefixed with standard 
    brand identifier tags.
    """
    text_to_format = invocation_state.get("saved_text", "")
    return f"*** BRAND OUTPUT ***\n{text_to_format.upper()}"


# Instantiate node entities mapping targets to custom function execution logic
interrupter_node = FunctionNode(ask_human, "interrupter")
saver_node = FunctionNode(save_file, "saver")
formatter_node = FunctionNode(format_output, "formatter")

# -------------------------------------------------------------------
# Build the Graph
builder = GraphBuilder()
builder.add_node(writer_agent, "writer")
builder.add_node(translator_agent, "translator")
builder.add_node(interrupter_node, "interrupter")
builder.add_node(saver_node, "saver")
builder.add_node(formatter_node, "formatter")

builder.add_edge("writer", "translator")
builder.add_edge("translator", "interrupter")


def should_save(state: GraphState) -> bool:
    """
    Conditional routing function checking if the user opted to save execution.
    """
    return _node_text(state, "interrupter").strip().lower() in ("y", "yes")


def should_skip(state: GraphState) -> bool:
    """
    Conditional routing function checking if the user opted to bypass file writing.
    """
    return not should_save(state)


builder.add_edge("interrupter", "saver", condition=should_save)
builder.add_edge("saver", "formatter")
builder.add_edge("interrupter", "formatter", condition=should_skip)

builder.set_entry_point("writer")
graph = builder.build()

# -------------------------------------------------------------------
# Worflow Execution
async def main():
    """
    Main asynchronous pipeline initialization function.
    """
    print("🎬 Starting multi-agent Ollama Workflow (Strands)...")

    result = await graph.invoke_async(
        "A high-performance organic energy drink for programmers."
    )

    print("\n🏁 [WORKFLOW EXECUTION COMPLETE]")
    print(f"Execution order: {[n.node_id for n in result.execution_order]}")
    print(_node_text(result, "formatter"))


if __name__ == "__main__":
    asyncio.run(main())