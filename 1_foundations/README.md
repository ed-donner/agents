# Week 1 — Foundations

**Goal:** Build intuition for LLMs and the core agentic patterns before touching any framework.

---

## Labs

### Lab 1 — First API Calls (`1_lab1.ipynb`)
- Setting up the development environment and configuring API keys
- Instantiating the OpenAI client and structuring messages (system / user / assistant)
- Making basic chat completions and comparing nano vs. mini model variants
- Exercise: identify a real-world business pain point suitable for an agentic solution

### Lab 2 — Multi-Provider LLM Calls & LLM-as-Judge (`2_lab2.ipynb`)
- Calling multiple LLM providers with the same prompt: OpenAI, Anthropic Claude, Google Gemini, DeepSeek, Groq, and local Ollama models
- Handling provider-specific differences (e.g. Anthropic's required `max_tokens`)
- Implementing the **LLM-as-judge** pattern — using an LLM to rank responses from other LLMs
- Parsing JSON evaluation results to compare model quality programmatically

### Lab 3 — Context Injection, Gradio UI & Output Evaluation (`3_lab3.ipynb`)
- Extracting text from PDF files with `pypdf`
- Building a system prompt enriched with external context (LinkedIn profile, summary file)
- Launching a chat interface with **Gradio** in a single line
- Evaluating LLM outputs with **Pydantic** models and adding **retry logic** when quality checks fail

### Lab 4 — Tool Use & The Agent Loop (`4_lab4.ipynb`)
- Defining tools with **JSON schemas** (name, description, parameters, required fields)
- Implementing the core **tool-call loop**: `while not done` — keep calling the LLM until it stops invoking tools
- Dispatching tool calls dynamically using `globals()`
- Sending real-time push notifications via **Pushover**
- Deploying to **HuggingFace Spaces** with secrets management

### Extra — Formalising the Agent Loop (`5_extra.ipynb`)
- Reinforcing the agent loop pattern with a planning + execution example (todo-list agent solving a math problem)
- Understanding that agents are systems where an LLM *controls* workflow by calling tools iteratively to reach a goal

---

## App — `app.py`

A personal website chatbot that puts all Week 1 concepts together:

- Loads Ed Donner's LinkedIn PDF and `summary.txt` to build a rich system prompt
- Impersonates the instructor and answers visitor questions in character
- Uses **two tools**:
  - `record_user_details` — captures visitor email + notes
  - `record_unknown_question` — logs any question the agent couldn't answer
- Both tools fire a **Pushover push notification** to the instructor's phone in real time
- Wrapped in a **Gradio** `ChatInterface` — one line launches the full web UI

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| API setup | Configuring `.env`, loading keys, instantiating clients |
| Multi-provider calls | OpenAI, Anthropic, Gemini, DeepSeek, Groq, Ollama |
| LLM-as-judge | Using one LLM to evaluate and rank outputs from others |
| Tool schemas | JSON schema definition for function tools |
| Agent loop | `while not done` loop that processes tool calls until a final response |
| Context injection | Embedding PDF/text content into the system prompt |
| Gradio UI | One-line chat interface launch |
| Structured outputs | Pydantic models for typed, validated LLM responses |
| Push notifications | Real-time alerts via Pushover API |
| Deployment | HuggingFace Spaces with secrets |

---

## Files

```
1_foundations/
├── 1_lab1.ipynb          # First API calls
├── 2_lab2.ipynb          # Multi-provider + LLM-as-judge
├── 3_lab3.ipynb          # Context injection + Gradio + evaluation
├── 4_lab4.ipynb          # Tool use + agent loop
├── 5_extra.ipynb         # Agent loop deep dive
├── app.py                # Personal website chatbot (capstone app)
└── community_contributions/  # Student variations and experiments
```
