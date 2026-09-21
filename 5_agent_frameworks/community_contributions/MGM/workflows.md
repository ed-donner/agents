# Agentics Workflows
The Pydantic AI and the Strands agents can do workflows, but they take pretty different shapes. Here's how each maps to what your `agent_framework` graph does (writer → translator → human approval gate → conditional save → formatted output, with MCP filesystem access).

## Pydantic AI (`pydantic_graph`)
Pydantic AI's `pydantic_graph` module is a typed graph library, conceptually close to what you already have — nodes are classes/functions with typed inputs/outputs, edges are inferred from return-type annotations (or built explicitly in the newer beta `GraphBuilder` API).

- **Agents as nodes**: each `BaseNode` can wrap a `pydantic_ai.Agent` call.
- **Conditional branching**: the beta API has explicit `g.decision()` / `g.match()` constructs for exactly your save/skip fork; the classic API does it by returning different node types from a node's `run()` method (e.g. return either a `SaveNode` or `FormatNode` instance) and the graph follows whichever type came back.
- **Human-in-the-loop**: supported via durable execution — a node can raise/return something that pauses the graph, waits for a real HTTP request or external event with the user's decision, and resumes from the same node. This is more "production async approval" than your script's blocking terminal `input()`, but you can also just call `input()` inside a node the same way if you don't need durability.
- **MCP tools**: Pydantic AI agents support MCP servers natively as tool sources, so your filesystem-MCP piece maps over directly.
- **State**: the graph carries a typed `State` dataclass passed to every node — closer to a straightforward dict/dataclass than the pending/commit buffer semantics in `agent_framework`.

It's a very natural fit — arguably a smaller, more Pythonic version of the same idea.

## Strands Agents (AWS)
Strands' `GraphBuilder` (in `strands.multiagent`) is also a good fit, with a slightly different flavor:

```python
from strands import Agent
from strands.multiagent import GraphBuilder

builder = GraphBuilder()
builder.add_node(writer_agent, "writer")
builder.add_node(translator_agent, "translator")
builder.add_node(router_fn, "router")          # plain function node
builder.add_node(saver_fn, "saver")
builder.add_node(formatter_fn, "formatter")

builder.add_edge("writer", "translator")
builder.add_edge("translator", "router")
builder.add_edge("router", "saver", condition=should_save)
builder.add_edge("saver", "formatter")
builder.add_edge("router", "formatter", condition=should_skip)

graph = builder.build()
result = graph("A high-performance organic energy drink for programmers.")
```

- **Conditional edges**: first-class — `add_edge(..., condition=fn)`, same shape as your `should_save`/`should_skip`.
- **Cycles**: Strands graphs explicitly support cyclic topologies too (review/revise loops), which `agent_framework` also supports but Strands documents it as a headline feature.
- **Custom/non-agent nodes**: you can add plain functions as nodes (not just `Agent` instances) — useful for your router/saver/formatter logic, same as your `Executor` subclasses.
- **Human-in-the-loop**: Strands has a dedicated "Human in the Loop" concept plus an **Interrupts** primitive and a built-in `handoff_to_user` tool that pauses execution, preserves context, and resumes when a human responds — more structured than a bare `input()` call, and it plugs into session persistence so a pause can survive a process restart.
- **MCP tools**: Strands has native MCP tool support (`Model Context Protocol (MCP) Tools` in their docs), same idea as your `FilesystemMCP`.
- **State**: state flows through `invocation_state` passed at graph invocation, and node output is automatically passed to dependent nodes — you wouldn't need the manual `ctx.set_state`/`ctx.get_state` dance, output propagation is built into edge semantics.

## Rough fit summary
| | `agent_framework` | Pydantic AI (`pydantic_graph`) | Strands (`GraphBuilder`) |
|---|---|---|---|
| Typed nodes/edges | yes | yes (very strict, Pydantic-validated) | looser, string node IDs |
| Conditional edges | yes | yes (decision/match, or type-based) | yes (`condition=` callable) |
| Cycles/loops | supported | supported | supported, well-documented |
| Human-in-loop | manual (`input()`) | durable-execution pause/resume | built-in interrupts + `handoff_to_user` |
| MCP tools | yes | yes | yes |
| Ecosystem bias | Microsoft/.NET-parity | framework-agnostic, FastAPI-style | AWS/Bedrock-centric, deploys well to Lambda/AgentCore |

---

## Pydantic AI Structured Outputs 
To get Structured Outputs using Python's [Pydantic AI](https://pydantic.dev/docs/ai/core-concepts/output/) framework, you pass a Pydantic model directly into the result_type parameter when initializing the Agent. [1, 2] 

Pydantic AI natively forces the underlying LLM to adhere to this structural constraint at the token-generation level, parsing and returning a fully typed Python object. [3, 4] 

### 1. Basic Structured Output Implementation
Define your data shape using Pydantic's BaseModel. You can add constraints and document the fields using Field, which the LLM uses as context for generation. [2, 3, 5] 
```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent

# Step 1: Define your structured output schema
class TaglineOutput(BaseModel):
    tagline: str = Field(description="The primary catchy 1-sentence slogan. No quotes.")
    keywords: list[str] = Field(description="3-4 SEO or brand keywords associated with the tagline.")
    tone_analysis: str = Field(description="A brief explanation of why this fits the marketing vibe.")

# Step 2: Pass the schema to result_type
writer_agent = Agent(
    'openai:gpt-4o',
    result_type=TaglineOutput, # This enforces structured outputs
    system_prompt="You are a professional creative marketer."
)

# Step 3: Run the agent
result = writer_agent.run_sync("Create a tagline for an eco-friendly water bottle.")

# The output is automatically parsed and fully typed into your Pydantic model
print(result.output.tagline)
print(result.output.keywords)
print(f"Type: {type(result.output)}")  # <class '__main__.TaglineOutput'>
```
### 2. Dynamically Overriding the Output Type Per Run
If you want an agent to usually return text but occasionally return a structured format on a specific call, you can override the schema dynamically inside your execution method by passing result_type directly to .run_sync() or .run().
```python
# The default agent returns regular text (str)
flexible_agent = Agent('openai:gpt-4o', system_prompt="You are a helpful assistant.")

# Force a specific run to use Structured Output
result = flexible_agent.run_sync(
    "Extract customer info from: Jane Doe, jane@example.com",
    result_type=TaglineOutput # Overriding for this call only
)
```
### 3. Streaming Partial Structured Responses
Pydantic AI shines when streaming data. You can stream partial structured text token-by-token using run_stream. As fields are populated sequentially by the model, you can read intermediate data frames safely. [6] 
```python
import asyncio

async def main():
    agent = Agent('openai:gpt-4o', result_type=TaglineOutput)
    
    # Use run_stream for asynchronous token streaming
    async with agent.run_stream("Create a tagline for a high-performance running shoe.") as response:
        async for partial_output in response.stream_output(debounce_by=0.1):
            # partial_output updates dynamically as fields are completed
            print(f"Live structure text: {partial_output.tagline}")

asyncio.run(main())
```
### Direct Feature Comparison

| Feature [2, 3, 5, 7, 8] | Mastra AI (TypeScript) | Pydantic AI (Python) |
|---|---|---|
| Validation Layer | Zod[](https://zod.dev/) | Pydantic V2 |
| Assignment Property | outputSchema (passed to .generate()) | result_type (passed to Agent() or .run()) |
| Result Location | result.object | result.output |
| Validation Context | Uses Zod descriptions | Uses Field(description="...") |

[1] [https://pydantic.dev](https://pydantic.dev/docs/ai/core-concepts/output/)
[2] [https://dev.to](https://dev.to/gabrielmrojas/building-smarter-ai-apps-the-pydantic-ai-way-type-safety-and-structured-responses-4do0)
[3] [https://www.youtube.com](https://www.youtube.com/watch?v=MfRSkBTNoQU)
[4] [https://dida.do](https://dida.do/blog/structured-outputs-with-openai-and-pydantic)
[5] [https://codesignal.com](https://codesignal.com/learn/courses/expanding-crewai-capabilities-and-integration/lessons/using-pydantic-models-for-structured-output)
[6] [https://www.youtube.com](https://www.youtube.com/watch?v=xYaFxIuFnTE)
[7] [https://pydantic.dev](https://pydantic.dev/docs/ai/api/pydantic-ai/agent/)
[8] [https://www.reddit.com](https://www.reddit.com/r/LLMDevs/comments/1isf8q1/what_is_your_ai_agent_tech_stack_in_2025/)
[9] [https://www.youtube.com](https://www.youtube.com/watch?v=cc50_ce64yw)

---

## Strands Agents SDK Structured Outputs 
To get structured outputs using the [Strands Agents SDK](https://strandsagents.com/) framework, you pass a validation schema during agent invocation. [1] 

Like other modern agent platforms, Strands uses Pydantic in Python and Zod in TypeScript to guarantee type-safe, validated objects. [2] 

### 1. In Python (Using Pydantic)
In Python, pass your model to the structured_output_model parameter when calling the agent. The validated result is then exposed directly under result.structured_output. [1, 2, 3, 4] 
```python
from pydantic import BaseModel, Field
from strands import Agent

# 1. Define your structure
class ProductTagline(BaseModel):
    tagline: str = Field(description="The primary catchy 1-sentence slogan.")
    keywords: list[str] = Field(description="3-4 SEO or brand keywords.")
    tone_analysis: str = Field(description="Brief explanation of the marketing vibe.")

# 2. Instantiate your Strands agent
agent = Agent()

# 3. Invoke with the structured_output_model argument
result = agent(
    "Create a marketing snippet for an eco-friendly water bottle",
    structured_output_model=ProductTagline
)

# 4. Access the parsed, fully-typed output safely
print(result.structured_output.tagline)
print(result.structured_output.keywords)
print(type(result.structured_output))  # <class '__main__.ProductTagline'>
```
### 2. In TypeScript (Using Zod)
For TypeScript applications, use the @strands-agents/sdk. Pass your Zod schema into the options object of agent.invoke(), and extract the parsed output from result.structured_output. [1, 2] 
```ts
import { Agent } from '@strands-agents/sdk';
import { z } from 'zod';

// 1. Define your Zod schema
const ProductTaglineSchema = z.object({
  tagline: z.string().describe('The primary catchy 1-sentence slogan.'),
  keywords: z.array(z.string()).describe('3-4 SEO or brand keywords.'),
  toneAnalysis: z.string().describe('Brief explanation of the marketing vibe.')
});

// 2. Instantiate your Strands agent
const agent = new Agent();

// 3. Invoke the agent passing structuredOutputSchema
const result = await agent.invoke('Create a marketing snippet for a smart coffee mug.', {
  structuredOutputSchema: ProductTaglineSchema
});

// 4. Extract fully-typed fields
console.log(result.structured_output.tagline);
console.log(result.structured_output.keywords);
```
### Core Mechanics & Direct Comparison
| Feature [1, 2, 3, 4, 5, 6] | Mastra AI | Pydantic AI | Strands Agents |
|---|---|---|---|
| Python Tooling | N/A | BaseModel ➔ result_type | BaseModel ➔ structured_output_model |
| TS Tooling | z.object() ➔ outputSchema | N/A | z.object() ➔ structuredOutputSchema |
| Where to read it | result.object | result.output | result.structured_output |
| Self-Correction | Throws error if fails | Throws error if fails | Built-in Auto-Retry: Automatically passes schema validation errors back to the LLM to fix structural mistakes on the fly. |

[1] [https://strandsagents.com](https://strandsagents.com/docs/examples/structured_output/)
[2] [https://strandsagents.com](https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/)
[3] [https://builder.aws.com](https://builder.aws.com/content/38oLeEDz9rpomVmcycQYCJtFBU0/structured-output-with-pydantic-and-strands-agents)
[4] [https://www.youtube.com](https://www.youtube.com/watch?v=W4OzzEvm7s0)
[5] [https://strandsagents.com](https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/)
[6] [https://aws.amazon.com](https://aws.amazon.com/blogs/devops/building-self-extending-cli-tools-with-aws-strands/)

---

## Microsoft Agent Framework Structured Outputs 
In the Microsoft Agent Framework (which unifies the enterprise features of [Semantic Kernel](https://devblogs.microsoft.com/agent-framework/using-json-schema-for-structured-output-in-net-for-openai-models/) and [AutoGen](https://microsoft.github.io/autogen/0.4.6/user-guide/agentchat-user-guide/tutorial/agents.html)), you can implement structured outputs using two core languages: C# and Python. [1, 2, 3, 4] 

The framework natively handles token-level structural enforcement and automatic object deserialization. [2] 

### 1. In C# / .NET
The Microsoft Agent Framework supports structured JSON formatting via two distinct strategies depending on whether your schema is known at compile time. [5] 
#### Option A: Type-Safe compilation using RunAsync<T>
Use the RunAsync<T> method on your agent instances. It natively handles complex models, lists, and primitives. [2, 5] 
```c#
using System.ComponentModel;
using Microsoft.AgentFramework.Agents;

// 1. Define your strongly-typed structure
public class ProductTagline
{
    [Description("The primary catchy 1-sentence slogan.")]
    public string Tagline { get; set; }

    [Description("3-4 SEO or brand keywords.")]
    public List<string> Keywords { get; set; }
}

// 2. Initialize a compatible agent (e.g., ChatClientAgent)
var agent = new ChatClientAgent(chatClient)
{
    Instructions = "You are a professional creative marketer."
};

// 3. Request your structured model directly 
// (The framework handles JSON schema generation and deserialization)
ProductTagline result = await agent.RunAsync<ProductTagline>(
    "Create a tagline for an eco-friendly water bottle."
);

Console.WriteLine(result.Tagline);
```
#### Option B: Dynamic schemas using ResponseFormat [6] 
If the data structure is built dynamically at runtime or represented as raw JSON string formats, configure the ResponseFormat property in AgentRunOptions or directly at agent setup. [5, 7] 
```csharp
using Microsoft.AgentFramework.Agents;
using Microsoft.Extensions.AI;

var agentOptions = new AgentRunOptions
{
    ResponseFormat = ChatResponseFormat.ForJsonSchema(typeof(ProductTagline))
};

var response = await agent.RunAsync("Your prompt here", agentOptions);
// Returns the raw, un-deserialized JSON string matching the layout
string rawJson = response.Text; 
```

### 2. In Python
In Python, the Microsoft Agent Framework leans heavily on Pydantic models for declaration. You supply the model via the response_format option parameter. [5, 6] 
```python
from pydantic import BaseModel, Field
from microsoft_agent_framework import ChatClientAgent, AgentRunOptions

# 1. Outline your schema
class ProductTagline(BaseModel):
    tagline: str = Field(description="The primary catchy 1-sentence slogan.")
    keywords: list[str] = Field(description="3-4 SEO or brand keywords.")

# 2. Setup your agent
agent = ChatClientAgent(
    chat_client=my_chat_client,
    instructions="You are a professional creative marketer."
)

# 3. Request output adhering to the Pydantic template
options = AgentRunOptions(response_format=ProductTagline)
result = await agent.run("Create a tagline for an eco-friendly water bottle.", options=options)

# Access the structured dictionary or model instance directly
print(result.content.tagline)
```
### Quick Framework Reference Matrix
| Capability [2, 5, 6, 7, 8, 9] | C# Implementation | Python Implementation |
|---|---|---|
| Primary Method | agent.RunAsync<T>() | agent.run(..., options) |
| Schema Foundation | Standard C# Classes (Type) | Pydantic BaseModel |
| Dynamic Fallback | ChatResponseFormat.ForJsonSchema() | Raw JSON mappings (dict) |
| Metadata Parsing | [Description] attribute annotations | Field(description="...") annotations |

[1] [https://devblogs.microsoft.com](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)
[2] [https://www.youtube.com](https://www.youtube.com/watch?v=_COZAvuKrBg)
[3] [https://www.youtube.com](https://www.youtube.com/watch?v=98mg5q8s8TA)
[4] [https://www.youtube.com](https://www.youtube.com/watch?v=ppwpWbJHp-4&t=50)
[5] [https://learn.microsoft.com](https://learn.microsoft.com/en-us/agent-framework/agents/structured-outputs)
[6] [https://learn.microsoft.com](https://learn.microsoft.com/en-us/agent-framework/agents/structured-outputs)
[7] [https://learn.microsoft.com](https://learn.microsoft.com/pt-br/agent-framework/agents/structured-outputs)
[8] [https://devblogs.microsoft.com](https://devblogs.microsoft.com/agent-framework/using-json-schema-for-structured-output-in-net-for-openai-models/)
[9] [https://systenics.ai](https://systenics.ai/blog/2024-10-25-using-structured-outputs-with-semantic-kernel/)
[10] [https://www.youtube.com](https://www.youtube.com/watch?v=8aPnghV9QAQ&t=1105)
