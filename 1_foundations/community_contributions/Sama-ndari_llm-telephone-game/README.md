# LLM Telephone Game (Week 1)

Semantic drift experiment: pass one message through a chain of LLMs and measure how meaning degrades.

Week 1 foundations contribution — multi-model calling + LLM-as-judge + embedding similarity.

## Chain

GPT-4o → Claude → Gemini → DeepSeek → Mixtral/Groq → Llama (Ollama local)

## Features

- Universal API wrapper (OpenAI, Anthropic, Google, Groq/DeepSeek, Ollama)
- Strict "repeater" system prompts
- Quantitative score: cosine similarity (SentenceTransformers)
- Qualitative score: GPT-4o judge (mutation / hallucination)
- Matplotlib drift chart

## Setup

```bash
cd 1_foundations/community_contributions/Sama-ndari_llm-telephone-game
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (do not commit):

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
# optional: GROQ / DeepSeek / local Ollama
```

Optional: run Ollama locally for the last hop (`ollama pull llama3`).

## Run

Open `llm_telephone_game.ipynb` and run all cells.

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev  
Related repo: https://github.com/Sama-ndari/llm-semantic-drift-analysis
