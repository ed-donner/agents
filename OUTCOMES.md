# Course Outcomes — AI Engineer Agentic Track

A complete breakdown of what you will be able to **do**, **build**, and **understand** by the end of this course.

---

## Week 1 — Foundations

### Skills Gained
- Call any LLM provider (OpenAI, Anthropic, Gemini, DeepSeek, Groq, Ollama) from Python
- Structure conversations correctly using system / user / assistant message roles
- Extract and inject external content (PDFs, text files) into LLM context
- Define tools with JSON schemas and handle tool calls in a loop
- Build and launch a chat UI with Gradio in a single line
- Deploy a working agent to HuggingFace Spaces with secrets management
- Send real-time push notifications from an agent via Pushover

### What You Can Build
- A personal AI assistant chatbot that answers questions based on your own documents
- An LLM evaluation harness that compares multiple models side-by-side using an LLM-as-judge
- A deployed web chatbot that captures visitor emails and logs unanswered questions

### Core Concept Mastered
> The **agent loop** — an LLM calls tools, processes results, and repeats until it produces a final answer. This is the foundation of every agentic system in the course.

---

## Week 2 — OpenAI Agents SDK

### Skills Gained
- Create, run, and debug agents using the OpenAI Agents SDK (`Agent`, `Runner`, `Trace`)
- Convert agents into reusable tools with `as_tool()`
- Implement agent handoffs — passing control from one agent to another
- Add input guardrails that intercept and block invalid requests before execution
- Use Pydantic models to enforce structured, typed LLM outputs
- Write async multi-agent pipelines with `async/await` and `asyncio.gather()`
- Integrate live web search with `WebSearchTool`
- Send real emails from an agent via SendGrid

### What You Can Build
- A cold sales email system with 3 competing agents and a selector that picks the best
- A full deep research pipeline: plan → search → synthesise → email report
- A guardrailed agent that rejects off-topic or unsafe queries automatically

### Core Concept Mastered
> **Agent composition** — agents calling other agents as tools, with handoffs and guardrails, forming pipelines that no single agent could handle alone.

---

## Week 3 — CrewAI

### Skills Gained
- Define agents and tasks declaratively in YAML — no boilerplate Python
- Run sequential crews where each agent's output feeds the next
- Set up hierarchical crews with a manager agent that delegates to specialists
- Integrate external search tools (SerperDev) into agents
- Use three-tier memory: long-term (SQLite), short-term (RAG/vector), entity memory
- Build custom CrewAI tools by subclassing `BaseTool`
- Produce typed results from a crew using Pydantic output schemas

### What You Can Build
- A multi-agent debate system (proposer → opposer → judge)
- A financial research pipeline (researcher → analyst → markdown report)
- A stock picking system with persistent memory, hierarchical delegation, and push notifications

### Core Concept Mastered
> **Declarative multi-agent crews** — describing *what* agents are and *what* tasks they do, letting the framework handle orchestration, memory, and tool routing automatically.

---

## Week 4 — LangGraph

### Skills Gained
- Model any workflow as a `StateGraph` with typed state, nodes, and edges
- Route between nodes conditionally based on LLM output (`tool_calls`, structured fields)
- Execute tool calls automatically with `ToolNode`
- Persist conversation state across sessions using `MemorySaver` and `SqliteSaver`
- Isolate multiple users/sessions with `thread_id`
- Run graphs asynchronously with `graph.ainvoke()`
- Automate browser interactions with Playwright inside a graph
- Build an evaluator node that judges output quality and triggers retries

### What You Can Build
- A stateful, memory-persistent AI assistant that remembers past conversations
- A browser-automating research agent that reads real web pages
- A self-correcting "Sidekick" agent: tries a task, evaluates the result, retries if needed

### Core Concept Mastered
> **State machine orchestration** — making every step of agent execution explicit, observable, and controllable through a graph of typed nodes and conditional edges.

---

## Week 5 — AutoGen

### Skills Gained
- Use AutoGen's AgentChat API to build agents quickly (`AssistantAgent`, `TextMessage`, `ModelClient`)
- Organise agents into teams with `RoundRobinGroupChat` and termination conditions
- Process images alongside text using `MultiModalMessage`
- Reuse LangChain tools inside AutoGen via `LangChainToolAdapter`
- Use the Core API to build message-driven agents (`RoutedAgent`, `@message_handler`)
- Register agents with a `SingleThreadedAgentRuntime` for in-process execution
- Scale agents across multiple machines using a gRPC distributed runtime

### What You Can Build
- An airline booking agent backed by a SQLite database
- A team of agents that analyse images and produce structured reports
- A distributed system where agents run in separate processes and coordinate over gRPC

### Core Concept Mastered
> **Message-driven architecture** — agents as independent processes that communicate purely through typed messages, enabling both local and distributed deployment without changing agent logic.

---

## Week 6 — Model Context Protocol (MCP)

### Skills Gained
- Understand what MCP is and why it matters as a universal agent-tool standard
- Spawn and use built-in MCP servers: fetch, Playwright, filesystem
- Discover server capabilities dynamically at runtime with `list_tools()`
- Build your own MCP server by wrapping any Python code with the MCP SDK
- Distinguish between MCP tools (callable actions) and MCP resources (readable data)
- Connect one agent to multiple MCP servers simultaneously
- Integrate real-world services: Brave Search, Polygon.io financial data, memory graph DB
- Apply smart caching to handle API rate limits gracefully

### What You Can Build
- An agent that browses the web, reads files, and writes files — all through MCP
- A custom MCP server exposing your own backend as agent-callable tools
- A financial agent connected to live market data, persistent memory, and web search
- A full trading floor simulator: multiple trader agents, account server, market server, push notification server

### Core Concept Mastered
> **Protocol-based tool integration** — decoupling agent logic from tool implementation so any agent can use any tool server, making your agents framework-agnostic and infinitely extensible.

---

## Cross-Cutting Outcomes

By the end of all 6 weeks you will be able to:

### Design
- Choose the right framework for any agentic use case (raw SDK vs. CrewAI vs. LangGraph vs. AutoGen vs. MCP)
- Design multi-agent topologies: sequential, parallel, hierarchical, graph-based, distributed
- Plan evaluation and retry strategies into agent architecture from the start

### Build
- Wire up any LLM provider to any tool using any major framework
- Implement persistent memory in agents using SQLite, RAG, or entity graphs
- Create async, non-blocking agent pipelines that run multiple agents concurrently
- Connect agents to real-world services: email, push notifications, web search, financial data

### Deploy
- Ship agents as Gradio web apps
- Deploy publicly to HuggingFace Spaces with secrets management
- Run agents as MCP servers consumable by any MCP-compatible client

### Understand
- How the agent loop works at every level — from raw API to high-level framework
- Why structured outputs and Pydantic models matter for reliability
- The tradeoffs between every major orchestration approach
- How MCP changes the agent-tool relationship from tight coupling to open protocol

---

## Frameworks & Tools You Will Have Hands-On Experience With

| Category | Tools |
|----------|-------|
| LLM Providers | OpenAI, Anthropic Claude, Google Gemini, DeepSeek, Groq, Ollama |
| Agent Frameworks | OpenAI Agents SDK, CrewAI, LangGraph, AutoGen |
| Protocol | Model Context Protocol (MCP) |
| UI | Gradio |
| Memory | SQLite, RAG/vector, entity memory, LangGraph checkpointers |
| External Services | Pushover, SendGrid, SerperDev, Brave Search, Polygon.io |
| Deployment | HuggingFace Spaces |
| Data | PDF parsing (pypdf), Pydantic, JSON schemas |
| Async | Python asyncio, gRPC |
| Browser | Playwright |
