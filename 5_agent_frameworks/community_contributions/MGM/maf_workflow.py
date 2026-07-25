import os
import asyncio
import subprocess
from pathlib import Path
from typing import Never

from dotenv import load_dotenv
from agent_framework import (
    WorkflowBuilder, WorkflowContext, Executor, AgentExecutor, AgentExecutorResponse, 
    Agent, handler, agent_middleware, function_middleware, MCPStdioTool
)
from agent_framework.openai import OpenAIChatCompletionClient

# Load environment configuration variables
load_dotenv(override=True)

# -------------------------------------------------------------------
# Establish target workspace directory structure for local file extraction
workspace = Path("workspace").resolve()
workspace.mkdir(exist_ok=True)

class FilesystemMCP(MCPStdioTool):
    """
    Custom Model Context Protocol (MCP) tool wrapper handling stdio client setup.
    
    Spawns an asynchronous connection to the external file system server 
    and sets the persistent working directory boundary to the resolved workspace.
    """
    def get_mcp_client(self):
        from mcp.client.stdio import StdioServerParameters, stdio_client
        params = StdioServerParameters(command=self.command, args=self.args, env=self.env, cwd=str(workspace))
        return stdio_client(server=params, errlog=subprocess.DEVNULL)

# Instantiate the standard filesystem server definition targeting Node Package Execute
filesystem = FilesystemMCP(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", str(workspace)],
)

# -------------------------------------------------------------------
# Observability Middleware Definition
@agent_middleware
async def notebook_chat_logger(context, next):
    """
    Intercepts and logs text communication states across active AI Agent operations.
    
    Prints initial initialization frames, parses recent inbound historical prompt text, 
    and prints out agent generation metrics upon downstream step finalization.
    """
    print(f"\n🚀 [AGENT INITIALIZED] Running task invocation...")
    if hasattr(context, 'messages') and context.messages:
        latest_msg = context.messages[-1]
        msg_text = getattr(latest_msg, 'text', None) or str(latest_msg)
        print(f"📥 [LATEST INPUT]: {msg_text}")
    await next()
    if hasattr(context, 'result') and context.result:
        result_text = getattr(context.result, 'text', None) or str(context.result)
        print(f"📤 [AGENT RESPONSE]: {result_text}")

@function_middleware
async def notebook_tool_logger(context, next):
    """
    Monitors, logs, and formats runtime information for external tool invocations.
    
    Intercepts function parameters before processing and slices oversized downstream 
    response data blocks to ensure optimal console readability.
    """
    print(f"\n🔧 [TOOL CALL] invoking: '{context.function.name}'")
    if hasattr(context, 'arguments') and context.arguments:
        print(f"   ↳ Arguments: {context.arguments}")
    await next()
    if hasattr(context, 'result') and context.result:
        print(f"   ✅ Result: {str(context.result)[:150]}...")

# -------------------------------------------------------------------
# Configure local inference endpoint client mapping to an OpenAI-compatible spec
ollama_client = OpenAIChatCompletionClient(
    model="qwen2.5:7b",
    base_url=os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1"),
    api_key="Ollama"
)

# -------------------------------------------------------------------
# Marketing agent specialized in short-form creative brand taglines
writer_agent = Agent(
    client=ollama_client,
    instructions="You are a professional creative marketer. Write a concise, 1-sentence product tagline. Do not use quotation marks.",
    name="WriterAgent",
    middleware=[notebook_chat_logger, notebook_tool_logger]
)

# -------------------------------------------------------------------
# Translation agent specialized in converting localized copy directly into Spanish
translator_agent = Agent(
    client=ollama_client,
    instructions="You are an expert translator. Translate the given text exactly into natural Spanish. Return only the final Spanish text.",
    name="TranslatorAgent",
    middleware=[notebook_chat_logger, notebook_tool_logger]
)

# -------------------------------------------------------------------
# TYPE-ANNOTATED ROUTER & INPUT INTERACTION NODES
#
# All four custom executors below use WorkflowContext[T] / WorkflowContext[T, U] generics on `ctx`, and send their outgoing 
# payload via ctx.send_message(...) (or ctx.yield_output(...) for the terminal node) rather than a bare `return`.
# This is what the framework's output validator inspects to know what each executor is allowed to produce - a bare `WorkflowContext` 
# (no brackets) or a handler that only `return`s a value will fail validation for output/intermediate executors.
# -------------------------------------------------------------------

class HumanDecisionInterrupter(Executor):
    """
    Workflow executor that pauses execution to secure manual user consensus.
    
    Safely unpacks varying agent responses, falls back to a structural default 
    on empty generation buffers, and forwards an interactive command choice map.
    """
    @handler
    async def ask_user(self, response: AgentExecutorResponse, ctx: WorkflowContext[dict]) -> None:
        extracted_text = ""
        if hasattr(response, "agent_response") and response.agent_response:
            extracted_text = getattr(response.agent_response, "text", "")
        elif hasattr(response, "agent_run_response") and response.agent_run_response:
            extracted_text = getattr(response.agent_run_response, "text", "")
        else:
            extracted_text = str(response)

        extracted_text = extracted_text.strip()
        if not extracted_text:
            extracted_text = "Una bebida energética orgánica de alto rendimiento para programadores."
            print("\n⚠️ Warning: The translator agent returned an empty response. Using pre-baked fallback string.")

        print(f"\n🔍 [TRANSLATION PREVIEW]:\n{extracted_text}")

        user_choice = input("💾 Would you like to save this translation to a file? (y/n): ").strip().lower()
        await ctx.send_message({"choice": user_choice, "text": extracted_text})


class WorkflowRouter(Executor):
    """
    Evaluates runtime states and assigns next-hop edge targets inside the workflow.
    
    Saves context string records into the global graph state mapping table 
    and publishes text flags evaluated by graph routing conditions.
    """
    @handler
    async def route_decision(self, data: dict, ctx: WorkflowContext[str]) -> None:
        ctx.set_state("saved_text", data.get("text", ""))
        decision = "save" if data.get("choice") in ["y", "yes"] else "skip"
        await ctx.send_message(decision)


class FileSaver(Executor):
    """
    Handles workflow pipeline persistence using standard context tool wrappers.
    
    Provides reliable, self-healing file creation by cascading from managed 
    MCP runtime client executions straight into native filesystem streams.
    """
    def __init__(self, filesystem_tool, **kwargs):
        super().__init__(**kwargs)
        self.fs = filesystem_tool

    @handler
    async def save_to_disk(self, data: str, ctx: WorkflowContext[str]) -> None:
        text_to_save = ctx.get_state("saved_text", "")
        print("\n🔧 [WORKFLOW INTEROP] Handing file operation over to MCP Filesystem...")

        try:
            result = await self.fs.call_tool(
                "write_file",
                path="maf_translate.txt",
                content=text_to_save,
            )
            print(f"✨ SUCCESS: MCP tool written to maf_translate.txt via tool lifecycle wrapper.")
            print(f"🔍 DEBUG: MCP result = {result!r}")
        except Exception as e:
            print(f"⚠️ Direct MCP method call failed ({e}). Falling back to manual write...")
            file_path = workspace / "maf_translate.txt"
            file_path.write_text(text_to_save, encoding="utf-8")
            print(f"✨ Fallback SUCCESS: File created at {file_path.resolve()}")

        await ctx.send_message(text_to_save)


class FinalFormatter(Executor):
    """
    The terminal node of the workflow graph that outputs the final brand presentation.
    
    Uses `Never` for outbound messages and yields a stylized, capitalized string 
    via `ctx.yield_output` to satisfy the framework's output validator requirements.
    """
    @handler
    async def format_output(self, response: str, ctx: WorkflowContext[Never, str]) -> None:
        text_to_format = ctx.get_state("saved_text", "")

        val = getattr(response, "value", response)
        if hasattr(val, "result"):
            val = val.result

        if str(val) not in ("skip", "save") and len(str(val)) > 5:
            text_to_format = str(val)

        final_string = f"*** BRAND OUTPUT ***\n{text_to_format.upper()}"
        await ctx.yield_output(final_string)

# -------------------------------------------------------------------
# COMPOSE THE GRAPH VIA STANDARD CONDITIONAL EDGES
writer_node = AgentExecutor(agent=writer_agent, id="writer_step")
translator_node = AgentExecutor(agent=translator_agent, id="translator_step")
interrupter_node = HumanDecisionInterrupter(id="interrupter_step")
router_node = WorkflowRouter(id="router_step")
saver_node = FileSaver(filesystem_tool=filesystem, id="saver_step")
formatter_node = FinalFormatter(id="formatter_step")

def should_save(edge_context) -> bool:
    """
    Returns True if the upstream router yielded a confirmation to save data.
    """
    val = getattr(edge_context, "value", edge_context)
    if hasattr(val, "result"): 
        val = val.result
    return "save" in str(val).lower()

def should_skip(edge_context) -> bool:
    """
    Returns True if the upstream router yielded a confirmation to skip saving.
    """
    val = getattr(edge_context, "value", edge_context)
    if hasattr(val, "result"): 
        val = val.result
    return "skip" in str(val).lower()

# -------------------------------------------------------------------
# Workflow Build
workflow = (
    WorkflowBuilder(start_executor=writer_node, output_from=[formatter_node])
    .add_edge(writer_node, translator_node)
    .add_edge(translator_node, interrupter_node)
    .add_edge(interrupter_node, router_node)
    
    .add_edge(router_node, saver_node, condition=should_save)
    .add_edge(saver_node, formatter_node)
    
    .add_edge(router_node, formatter_node, condition=should_skip)
    .build()
)

# -------------------------------------------------------------------
# Workflow Execution
async def main():
    print("🎬 Starting multi-agent Ollama Workflow...")
    
    async with filesystem:
        result = await workflow.run("A high-performance organic energy drink for programmers.")
    
    print("\n🏁 [WORKFLOW EXECUTION COMPLETE]")
    outputs = result.get_outputs()
    if outputs:
        print(outputs[-1])
    else:
        print("No output generated:", result)


if __name__ == "__main__":
    asyncio.run(main())