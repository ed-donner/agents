# AI Interview Simulator (Week 1)

Streamlit interview chatbot with OpenAI. Collects a candidate profile, runs an adaptive HR-style chat (up to 5 turns), then scores and feedbacks the interview.

Week 1 patterns: chat UI, system prompts, streaming completions, session state, post-conversation evaluation.

## Flow

1. Profile setup (name, experience, skills, level, role, company)
2. Interview chat (GPT-4o, streaming)
3. Feedback (score 1–10 + structured notes)
4. Restart

## Run

```bash
cd 1_foundations/community_contributions/Sama-ndari_interview-tool
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdir -p .streamlit
echo 'OPENAI_API_KEY = "sk-..."' > .streamlit/secrets.toml
streamlit run app.py
```

Do not commit `.streamlit/secrets.toml` (see `.gitignore`).

Full project (optional): https://github.com/Sama-ndari/Interview-tool

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
