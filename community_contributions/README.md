# Community Contributions — SaintChris

## About Me

- **Name:** Alex (SaintChris)
- **GitHub:** [@SaintChris](https://github.com/SaintChris)
- **Portfolio:** [saintlex.sbs](https://saintlex.sbs)
- **Location:** Jamaica

## Course

**AI Engineer Agentic Track: The Complete Agent & MCP Course** by Ed Donner  
[Course Link](https://www.udemy.com/course/ai-engineer-agentic-track/) | [Repo](https://github.com/ed-donner/agents)

## Contributions

### Week 1 — Foundations

#### Lab 1: Environment Setup with OpenRouter
- Set up the course environment using **OpenRouter** instead of direct OpenAI
- All API calls routed through OpenRouter's free models
- Exercise: Designed a 7-agent architecture for Legal Document Review

#### Lab 2: Multi-Model Competition
- Ran multi-model competition using 6 free models via OpenRouter
- Implemented rate limit handling with retries and delays
- LLM-as-judge pattern to rank responses

#### Lab 3: LinkedIn Chatbot with Gradio
- Built a chatbot that answers questions about a LinkedIn profile
- Used pypdf to parse PDF, Gradio for UI
- Evaluation loop with rerun pattern

#### Lab 4: Tool Use & Deployment
- Added tool calling (record user details, record unknown questions)
- Pushover integration for phone notifications
- Deployment to HuggingFace Spaces

#### Lab 5 (Extra): Agent Loop from Scratch
- Built a minimal agent without any framework
- Pattern: LLM + tools + while loop = agent

## Key Patterns Learned

1. **Prompt Chaining** — sequential LLM calls
2. **Routing** — classify and route to specialists
3. **Parallelization** — run independent tasks simultaneously
4. **Orchestrator-Worker** — manager delegates to specialists
5. **Evaluator-Optimizer** — generate, evaluate, improve in a loop

## Setup Notes

```bash
cd agents
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install python-dotenv openai pypdf gradio requests ipykernel
```

## Contact

- GitHub: [@SaintChris](https://github.com/SaintChris)
- Portfolio: [saintlex.sbs](https://saintlex.sbs)
- Email: bogle.alex@hotmail.com
