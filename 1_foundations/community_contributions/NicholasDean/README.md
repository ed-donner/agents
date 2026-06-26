# Nicholas Dean - Week 1 (Foundations)

A minimal "career conversation" agent built with no framework - the raw tool-calling loop.

- `career_conversation.py` - answers as me, with two tools (record an interested visitor's
  email, record an unknown question) that push to my phone via Pushover.
- `me.md` - the short bio it answers from.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python career_conversation.py` (needs `OPENAI_API_KEY`; `PUSHOVER_*` optional).
