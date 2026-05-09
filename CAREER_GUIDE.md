# Career Guide — .NET + React Developer Transitioning to AI Engineering

> **Your profile:** 6 years full-stack experience (.NET backend + React frontend), 2 hours/day available for learning.

---

## Your Existing Strengths That Transfer Directly

Before talking about what you gain — you already have massive advantages others in this course don't:

| Your Skill | Why It Matters in Agentic AI |
|---|---|
| **.NET backend** | You understand APIs, async patterns, dependency injection, service layers — MCP servers are just that |
| **React frontend** | Gradio is trivial for you. You can replace it with a proper React UI immediately |
| **REST APIs** | Every LLM provider (OpenAI, Anthropic) is just an HTTP API — you'll move faster than pure ML people |
| **6 years experience** | You understand production code, error handling, logging — things most AI tutorials skip entirely |
| **C# async/await** | Python's async/await is identical in concept — Week 2 and 4 async labs will feel familiar |

---

## What You Specifically Gain

### 1. A Completely New Billable Skill
AI engineering is the fastest-growing job category right now. You're not starting from zero — you're adding a layer on top of 6 years of solid engineering. That's the most hireable profile possible: someone who can build AI features *and* integrate them into real production systems.

### 2. You Can Build What .NET/React Devs Are Being Asked to Build Right Now
Every enterprise .NET shop is being asked:
- *"Can we add an AI chatbot to our internal tools?"*
- *"Can we automate this workflow with AI?"*
- *"Can we build a Copilot for our product?"*

After this course you can say **yes** to all three — and actually deliver it.

### 3. MCP Is Your Biggest Win
As a backend developer, Week 6 (MCP) is where you'll shine. MCP is essentially *"expose your existing .NET APIs as agent-callable tools."* You already know how to build the backend — now you know how to make it agent-accessible. This is exactly what companies need and very few people can do yet.

### 4. LangGraph Matches Your Mental Model
State machines, conditional routing, typed state — this is how .NET developers already think (workflow engines, finite state automata). LangGraph will feel natural to you in a way it won't for someone from a data science background.

---

## Interview Impact

### Roles You Can Now Apply For

| Role | Salary Range (approx) | What from this course applies |
|---|---|---|
| AI Engineer | $120k–$180k | Everything — all 6 weeks |
| Full-Stack AI Developer | $110k–$160k | Weeks 1–2 + your React/.NET stack |
| AI Solutions Architect | $150k–$200k | Framework comparison, MCP, multi-agent design |
| Senior .NET Developer + AI | $130k–$170k | MCP servers, tool integration, .NET + agent bridging |

### Interview Questions You Can Now Answer

- *"How would you add AI to our existing .NET microservices?"* → MCP server wrapping your existing services
- *"What's the difference between LangChain, CrewAI, and LangGraph?"* → You've used all three, you can compare tradeoffs
- *"How do you prevent an AI agent from doing something wrong?"* → Guardrails, input validation, evaluator pattern
- *"How would you build a multi-agent system?"* → Sequential, hierarchical, graph-based — you know all three
- *"What is MCP?"* → Most candidates won't know this yet. You will.

### Portfolio Projects You Can Show
1. A deployed personal AI assistant (HuggingFace Spaces) — live URL to show
2. A multi-agent research pipeline that sends real emails
3. A LangGraph agent with persistent memory and self-correction
4. A custom MCP server — extremely rare on a CV right now

---

## Career Path (Specific to You)

**Short term (0–6 months)**
Take what you build in this course and port one project to .NET. Rebuild the Week 6 MCP accounts server as a C# ASP.NET API exposed via MCP. This makes you unique: the person who bridges the .NET enterprise world and agentic AI.

**Medium term (6–18 months)**
Position yourself as the AI integration specialist at your current or next company. Most enterprises have massive .NET codebases and zero idea how to make them AI-capable. You are the bridge.

**Long term**
AI Solutions Architect or Principal AI Engineer. The people who will command the highest salaries are not pure ML researchers — they're engineers who understand systems, integrate AI into existing infrastructure, and evaluate framework tradeoffs. That's exactly what 6 years of .NET/React + this course builds.

---

## 2 Hours/Day Study Plan — Complete in 6 Weeks

> Total estimated time: ~80 hours across 6 weeks
> Daily commitment: 2 hours/day, 5 days/week (weekends optional for catch-up)

---

### Week 1 — Foundations (10 hours)

| Day | Task | Time |
|-----|------|------|
| Mon | Python syntax crash course (if needed) — focus on classes, async, type hints | 2h |
| Tue | Lab 1 — First API calls. Set up `.env`, call OpenAI, compare models | 2h |
| Wed | Lab 2 — Multi-provider calls + LLM-as-judge pattern | 2h |
| Thu | Lab 3 — PDF context injection + Gradio UI + Pydantic evaluation | 2h |
| Fri | Lab 4 + Extra — Tool schemas, agent loop, deploy to HuggingFace | 2h |

**Week 1 Goal:** Understand the agent loop cold. Be able to explain it without notes.

---

### Week 2 — OpenAI Agents SDK (10 hours)

| Day | Task | Time |
|-----|------|------|
| Mon | Lab 1 — Agent / Runner / Trace basics | 2h |
| Tue | Lab 2 — `as_tool()`, handoffs, SendGrid email pipeline | 2h |
| Wed | Lab 3 — Multi-model support, Pydantic outputs, input guardrails | 2h |
| Thu | Lab 4 — Async deep research pipeline (planner → search → write → email) | 2h |
| Fri | **Build day** — Modify Lab 4 to research a topic relevant to your work | 2h |

**Week 2 Goal:** Build one multi-agent pipeline you can demo in an interview.

---

### Week 3 — CrewAI (10 hours)

| Day | Task | Time |
|-----|------|------|
| Mon | Setup + run Debate crew. Read the YAML configs carefully | 2h |
| Tue | Financial Researcher crew — understand SerperDev tool integration | 2h |
| Wed | Stock Picker crew — study memory system and hierarchical process | 2h |
| Thu | **Build day** — Create your own crew for a domain you know (e.g. .NET code reviewer crew) | 2h |
| Fri | Compare CrewAI vs. OpenAI SDK — when would you use each? Write notes | 2h |

**Week 3 Goal:** Understand declarative vs. imperative agent design tradeoffs.

---

### Week 4 — LangGraph (12 hours)

> This is the most important week for you as a .NET developer. Spend extra time here.

| Day | Task | Time |
|-----|------|------|
| Mon | Lab 1 — StateGraph, TypedDict, nodes, edges. Draw the graph on paper | 2h |
| Tue | Lab 2 — Tool binding, conditional edges, MemorySaver checkpointing | 2h |
| Wed | Lab 3 — Async graph execution + Playwright browser automation | 2h |
| Thu | Lab 4 — Multi-node Sidekick + evaluator pattern (read this code very carefully) | 2h |
| Fri | **Build day** — Add a new tool to the Sidekick and test the evaluator loop | 2h |
| Sat (optional) | Map LangGraph concepts to .NET equivalents (StateGraph → Workflow, edges → routing) | 2h |

**Week 4 Goal:** Be able to design a state machine agent on a whiteboard from scratch.

---

### Week 5 — AutoGen (10 hours)

| Day | Task | Time |
|-----|------|------|
| Mon | Lab 1 — AgentChat basics, SQLite airline booking agent | 2h |
| Tue | Lab 2 — Multimodal messages, RoundRobinGroupChat, MCP integration | 2h |
| Wed | Lab 3 — AutoGen Core: RoutedAgent, message handlers, runtime | 2h |
| Thu | Lab 4 — Distributed gRPC runtime across processes | 2h |
| Fri | Compare all 4 frameworks. Build a cheat sheet: when to use what | 2h |

**Week 5 Goal:** Understand message-driven architecture — map it to .NET's `IHostedService` / message bus patterns you already know.

---

### Week 6 — MCP (12 hours)

> This week is your biggest career differentiator as a .NET developer.

| Day | Task | Time |
|-----|------|------|
| Mon | Lab 1 — Spawn built-in MCP servers, call `list_tools()`, browse with MCP | 2h |
| Tue | Lab 2 — Build your own MCP server wrapping Python code | 2h |
| Wed | Lab 3 — Brave Search + Polygon.io + memory graph DB ecosystem | 2h |
| Thu | Study the trading floor simulator — read all server files | 2h |
| Fri | **Build day** — Wrap a mock .NET-style REST API as an MCP server in Python | 2h |
| Sat (optional) | Research: how to build an MCP server in C# (community packages exist) | 2h |

**Week 6 Goal:** Ship one custom MCP server you built yourself. Add it to your portfolio.

---

## After the Course — 4 Week Portfolio Sprint

Once the 6 weeks are done, spend 4 more weeks building one capstone project to put on your CV:

### Suggested Capstone: ".NET Codebase AI Assistant"
An agent that can:
- Read your .NET solution files and understand the architecture
- Answer questions about the codebase
- Suggest refactors or identify bugs
- Exposed via MCP so any agent framework can use it

This is immediately relatable to any .NET hiring manager and demonstrates every skill from the course.

| Week | Focus |
|------|-------|
| Week 7 | Build the MCP server that reads .NET project files |
| Week 8 | Build the agent (LangGraph) with memory + evaluator |
| Week 9 | Add React frontend (your existing skill) replacing Gradio |
| Week 10 | Polish, deploy, write a short blog post about it |

---

## One Honest Caution

This course is in **Python**. If you're not already comfortable with Python basics, spend the first 2 days on:
- Classes and `__init__`
- `async/await` (same as C# conceptually)
- Type hints and Pydantic (same as C# generics + data annotations)
- `pip` / `uv` (same as NuGet)

The concepts will be instantly familiar from your C# background. Only the syntax is new.

---

## Quick Reference — .NET to Python Mental Map

| C# / .NET | Python Equivalent |
|---|---|
| `async Task` | `async def` |
| `IEnumerable<T>` | `List[T]` |
| `record` / `DataAnnotations` | `Pydantic BaseModel` |
| `IServiceCollection` (DI) | Constructor injection / `globals()` |
| `appsettings.json` | `.env` + `python-dotenv` |
| `IHostedService` | `asyncio` event loop |
| NuGet | `pip` / `uv` |
| State machine (Workflow) | LangGraph `StateGraph` |
| Minimal API endpoint | MCP `@mcp.tool()` |
| `HttpClient` | `requests` / `httpx` |

---

## Bottom Line

You are not a beginner learning AI. You are an experienced engineer adding the most in-demand specialisation of 2025–2026 to a strong foundation. At 2 hours/day you can be interview-ready in **6 weeks** and portfolio-ready in **10 weeks**. That's the best possible position to be in.
