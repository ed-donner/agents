# Digital twin with a reviewer

Week 1 day 4 exercise: a career chatbot that answers questions about me, with a second LLM sitting
between the twin and the visitor. The reviewer reads every reply before it's sent and holds back
anything off topic or unsupported by my profile. Held replies get rewritten once, with the reason
attached.

## Why bother

The twin's system prompt already says "stay on professional topics", and it mostly works. Two things
it can't do:

- The system prompt is written before the reply exists. A reviewer reads the actual output.
- The twin is simultaneously being told to be warm, engaging, helpful and on topic. Every extra rule
  waters down the others. A separate call gets a clean context and exactly one job.

## How it works

```
visitor message
      |
      v
  twin (gpt-5.4-mini) --> tool calls --> agent loop until no more tools
      |
      v
  draft reply
      |
      v
  reviewer (gpt-5.4-nano) --> PASS ------> send
      |
      FAIL: reason
      |
      v
  twin rewrites once, with the rejected reply and the reason in its prompt --> send
```

One retry, not a loop. If the twin and the reviewer disagree on principle they never converge, and
each extra round is two more API calls while someone watches a spinner. A reply that fails twice
rarely passes on the third go.

## Two things worth knowing if you build your own

**PASS / FAIL, not ACCEPTABLE / UNACCEPTABLE.** "UNACCEPTABLE" contains "ACCEPTABLE" as a substring,
so `"ACCEPTABLE" in verdict` reads every rejection as approval. Not occasionally wrong - wrong every
time, in exactly the case the reviewer exists for. You'd watch it never reject anything and assume
the twin was well behaved.

**It fails open.** If the verdict parses as neither PASS nor FAIL, the reply goes out and a warning
prints. Failing closed would mean a parsing hiccup silently doubles latency and cost on every
message, with nothing in the logs. The twin's own system prompt is still the primary constraint;
the reviewer is a second layer, and a broken second layer shouldn't degrade the experience for
everyone.

That string parsing is the weak point either way. Structured outputs are the real fix.

## Running it

```bash
cd 1_foundations/community_contributions/sev_rudakov_twin_evaluator
uv run jupyter lab 3_lab3_evaluator.ipynb
```

Needs `OPENAI_API_KEY` in a `.env` at the project root. Run the cells top to bottom; the last one
launches the Gradio UI, and everything the twin and reviewer do prints under the cells as you chat.

There are two test cells before the UI. The first sends a real question through the full pipeline
and shows the reviewer passing it. The second feeds the reviewer a hand-written bad reply, because
the twin won't reliably misbehave on request - ask it about politics and it usually steers back on
its own, which passes. You need a deliberately bad fixture to exercise the failure path at all.

## Files

```
3_lab3_evaluator.ipynb   the whole thing
me/linkedin.pdf          LinkedIn export
me/summary.txt           the things a LinkedIn export doesn't cover
requirements.txt
```

Recorded emails append to `emails.txt`, which is gitignored. Swap `record_email_tool` for a push
notification or a database if you're running this anywhere real.
