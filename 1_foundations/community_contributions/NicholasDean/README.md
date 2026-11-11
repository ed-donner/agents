# Nicholas Dean - Week 1 (Foundations)

"Professionally You" - the full week-1 capstone: a career-conversation agent built with no
framework, deployable to HuggingFace Spaces.

- `app.py` - answers as me with two tools (record an interested visitor's email, record an
  unknown question) that push to my phone via Pushover; runs the tool-calling loop; and adds an
  evaluator-optimizer pass (a second model grades each reply and a rejected one is regenerated
  with the feedback before the visitor sees it).
- `me.md` - the short bio it answers from.
- `requirements.txt` - dependencies for the Space.
- `SUMMARY.md` - what I learned this week.

Run locally: `uv run python app.py` (needs `OPENAI_API_KEY`; `PUSHOVER_*` optional).
Deploy: `uv run gradio deploy` from this folder (entry point `app.py`), then set the secrets.
