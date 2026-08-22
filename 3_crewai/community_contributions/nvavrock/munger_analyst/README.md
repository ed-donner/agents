# Munger Analyst

Value-oriented equity memo crew using Charlie Munger’s mental models (BLUF: verdict first), plus an optional chatbot that can follow up on saved memos.

Educational analysis only — **not financial advice**.

## What’s unique

| Piece | Detail |
|-------|--------|
| Lens | Value investing + Munger latticework (knowledge RAG) |
| Memo format | BLUF verdict first; `output/YYYYMMDD_<company>_memo.md` |
| Chat | `uv run chat` — analyze or Q&A against saved memos |

## Setup

```bash
cd 3_crewai/community_contributions/nvavrock/munger_analyst
cp .env.example .env   # add OPENAI_API_KEY and SERPER_API_KEY
uv tool install crewai==1.14.4   # if needed
crewai install
```

## Run

One-shot memo:

```bash
crewai run
```

Chat (follow-ups on session or `output/*_memo.md`):

```bash
uv run chat
```

## Layout

```
munger_analyst/
├── knowledge/          # Munger models + personal model stubs
├── src/munger_analyst/
│   ├── config/         # agents.yaml, tasks.yaml
│   ├── crew.py
│   ├── main.py
│   └── memo_naming.py
└── pyproject.toml
```
