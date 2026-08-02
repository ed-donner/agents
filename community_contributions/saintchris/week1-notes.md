# Week 1 — Study Notes

## Lab 1: Environment Setup & First API Calls

### Setup
```bash
cd agents
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install python-dotenv openai pypdf gradio requests ipykernel
```

Create a `.env` file in the project root with your API key:
```
OPENAI_API_KEY=your-key-here
```

### Key Learnings
- **OpenAI SDK works with any OpenAI-compatible provider** — just change `base_url`
- **Free models** work for learning but have rate limits — have fallbacks ready
- **Core pattern:** load env → create client → build messages → call API → read response

### Reusable Code Pattern
```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)
client = OpenAI(base_url="https://openrouter.ai/api/v1")

response = client.chat.completions.create(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    messages=[{"role": "user", "content": "Your prompt"}]
)
print(response.choices[0].message.content)
```

### Exercise: Agentic AI Business Opportunity
Used 3 LLM calls to:
1. Pick a business area (Legal Document Review)
2. Identify a pain point (inconsistent legal judgments across large document sets)
3. Design a solution (7-agent architecture with Case-Model Architect, Context-Seeker, Judgment-Consistency Monitor, Risk-Synthesizer, Human-Liaison, Supervisor, and Learning Agent)

---

## Lab 2: Multi-Model Competition

### Goal
Ask the same question to multiple LLMs, then have a judge LLM rank the responses.

### Pattern
```
Question → [Model 1] → Response 1 ─┐
          → [Model 2] → Response 2 ─┤
          → [Model 3] → Response 3 ─┘
                                      ↓
                              Judge LLM ranks all
                                      ↓
                              Final Rankings (JSON)
```

### Free Models Available on OpenRouter
- `openai/gpt-oss-120b:free`
- `nvidia/nemotron-3-super-120b-a12b:free`
- `google/gemma-4-26b-a4b-it:free`
- `qwen/qwen3-coder:free`
- `meta-llama/llama-3.2-3b-instruct:free`
- `nousresearch/hermes-3-llama-3.1-405b:free`

### Tips
- Add 60s delays between calls to avoid rate limits
- Shorter questions = faster responses = less throttling
- Implement retry logic with exponential backoff
- The LLM-as-judge pattern is how you evaluate AI systems in production

---

## 5 LLM Workflow Design Patterns

### 1. Prompt Chaining
Break a complex task into sequential LLM calls. Each output becomes the next input.
- **Use when:** Multi-step reasoning, validation between steps
- **Pros:** Focused steps, easier to debug
- **Cons:** Latency adds up, errors compound

### 2. Routing
Classify input → route to specialized handler.
- **Use when:** Different input types need different handling
- **Pros:** Each handler is optimized, can use different models per route
- **Cons:** Router can misclassify

### 3. Parallelization
Run independent subtasks simultaneously, combine results.
- **Use when:** Speed matters, multiple perspectives needed
- **Types:** Sectioning (split task) or Voting (multiple attempts)
- **Pros:** Faster than sequential, redundancy improves quality
- **Cons:** More API calls, combining results can be tricky

### 4. Orchestrator-Worker
Central orchestrator breaks down task → delegates to workers → synthesizes.
- **Use when:** Complex tasks, different worker expertise needed
- **Pros:** Scales well, workers are specialized
- **Cons:** Orchestrator is single point of failure

### 5. Evaluator-Optimizer
Generator LLM creates output → Evaluator LLM checks → loop until quality threshold.
- **Use when:** Quality-critical outputs, code generation
- **Pros:** Dramatically improves quality, self-correcting
- **Cons:** Multiple API calls, can get stuck in loops

---

## Agentic AI Frameworks Landscape

### Complexity Hierarchy

| Level | Framework | Notes |
|-------|-----------|-------|
| 1 | No Framework | Direct API calls, full control |
| 1.5 | MCP | Protocol (not framework), open standard |
| 2 | OpenAI Agents SDK | Lightweight, flexible, new |
| 2 | CrewAI | Lightweight, YAML config, low-code angle |
| 3 | LangGraph | Heavyweight, graph-based, steep learning curve |
| 3 | AutoGen | Heavyweight, Microsoft, group chats |

### Key Trade-offs
- **Lightweight** (OpenAI SDK, CrewAI): Stay out of your way, you control the code
- **Heavyweight** (LangGraph, AutoGen): More power, but you buy into their ecosystem

### Course Coverage
| Week | Framework |
|------|-----------|
| 1 | No framework (direct API) |
| 2 | OpenAI Agents SDK |
| 3 | CrewAI |
| 4 | LangGraph |
| 5 | AutoGen |
| 6 | MCP |

---

## Glossary

### Abbreviations
| Abbrev | Full Form |
|--------|-----------|
| LLM | Large Language Model |
| API | Application Programming Interface |
| SDK | Software Development Kit |
| RAG | Retrieval-Augmented Generation |
| MCP | Model Context Protocol |
| JSON | JavaScript Object Notation |
| YAML | YAML Ain't Markup Language |
| venv | Virtual Environment |
| BYOK | Bring Your Own Key |

### Key Terms
- **Agentic AI:** AI that reasons, plans, and acts autonomously
- **Agent:** LLM + role + goal + tools + memory
- **Task:** Unit of work with description and expected output
- **Crew:** Collection of agents and tasks working together
- **Tool:** Function an agent can call (search, code, APIs)
- **System Prompt:** Instructions prepended to every conversation
- **Chain of Thought:** LLM reasons step-by-step before answering
- **Token:** Piece of text the LLM processes (~3/4 of a word)
- **Hallucination:** LLM generates plausible but incorrect information
- **Temperature:** Controls randomness (0 = deterministic, 1 = creative)
- **Rate Limiting:** API providers limit requests per minute/hour

### Frameworks
- **OpenAI Agents SDK:** Lightweight, official OpenAI framework
- **CrewAI:** Role-based multi-agent framework with YAML config
- **LangGraph:** Graph-based agent workflows from LangChain
- **AutoGen:** Microsoft's multi-agent framework
- **MCP:** Model Context Protocol — open standard for tool integration
- **OpenRouter:** API gateway for 100+ LLMs through one interface
- **Ollama:** Run LLMs locally on your machine
- **Gradio:** Quick web UIs for ML models
- **uv:** Fast Python package manager (Rust-based)
- **pypdf:** Read PDF files in Python
- **python-dotenv:** Load environment variables from .env files

### Course Patterns
**Agent Loop:**
```
while not done:
    response = llm.call(messages, tools)
    if response.has_tool_calls():
        results = execute_tools(response.tool_calls)
        messages.append(results)
    else:
        done = True
return response
```

**Evaluation Pattern:**
```
answer = llm.answer(question)
evaluation = llm.evaluate(answer, question)
if evaluation.rejected:
    answer = llm.rerun(question, feedback=evaluation.feedback)
```

**Rerun Pattern:**
```
updated_prompt = system_prompt + "\n\nPrevious answer was rejected: {feedback}"
new_answer = llm.answer(question, system_prompt=updated_prompt)
```
