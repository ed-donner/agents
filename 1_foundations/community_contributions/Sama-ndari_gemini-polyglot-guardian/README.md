# Gemini Polyglot Guardian (Week 1)

Multilingual content-safety pipeline with Google Gemini + Gradio.

Analyzes text in any language (including low-resource languages like Kirundi / Swahili), then classifies risk: Safe, Misinformation, Scam, Hate Speech, Manipulation.

## Stack

- Google GenAI (Gemini)
- Gradio UI
- Optional LangGraph multi-agent flow (see notebook)

## Setup

```bash
cd 1_foundations/community_contributions/Sama-ndari_gemini-polyglot-guardian
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (do not commit):

```
GEMINI_API_KEY=your_key
```

## Run

Open `gemini_polyglot_guardian.ipynb` and run all cells (launches Gradio).

Full project (optional): https://github.com/Sama-ndari/gemini-polyglot-guardian

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
