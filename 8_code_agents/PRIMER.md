# Week 8 Primer — Code Agents: Write, Run, Test, Fix

> Read before the labs. The course showed CrewAI's coder agent as a demo. This
> week teaches the *actual mechanism* behind every code-writing agent (Copilot,
> Cursor, Claude Code, Devin): a closed feedback loop where the agent runs its own
> code and fixes its own failures.

---

## The one mental model

A code agent is the **agent loop (Week 1) with the compiler/test-runner as the tool**. The breakthrough idea is that code is *uniquely verifiable* — unlike an essay, you can *run* it and get objective feedback. So the loop closes on itself:

```
   ┌────────────────────────────────────────────────┐
   │                                                │
   ▼                                                │
 ┌──────┐   code   ┌─────────┐  pass/fail  ┌──────┐ │
 │ LLM  │─────────▶│ SANDBOX │────────────▶│ tests│ │
 │      │          │ (run it)│             └──┬───┘ │
 └──────┘          └─────────┘                │     │
   ▲                                    fail: feed  │
   │                                    pytest output│
   └──────────── "here's the error, fix it" ◀───────┘
                            pass → done
```

The objective signal (test results) is what makes code agents work where pure-text agents flail. The loop is: **generate → execute in a sandbox → run tests → if fail, feed the error back → repeat** (bounded by max iterations *and* max cost).

---

## Key concepts, precisely

**The sandbox (`sandbox.py`).** Untrusted, LLM-written code must NOT run in your process. Use `subprocess` isolation with a hard **timeout** and captured stderr — never `exec()`. This is a security boundary, not a convenience. `run_pytest()` writes the solution + tests to a temp dir and runs pytest, returning structured pass/fail output.

**The write→test→fix loop (`code_agent.py`).** Generate an initial solution, run the tests, and on failure build a fix prompt = *pytest output + current code + "fix it."* Loop until green or you hit `max_iterations` / `max_cost_usd`. **Bounding on cost is the senior move** — an agent that loops on an impossible test can otherwise burn unlimited money.

**AST-aware editing (`git_agent.py`, Lab 3).** For real codebases you don't regenerate whole files — you make *surgical* edits. Use Python's `ast` module to (a) understand structure before editing and (b) **validate that generated code parses** before you ever run or commit it. Committing syntactically invalid code is unforgivable; `ast.parse()` is the cheap guard.

**Git integration (Lab 4).** Read repo → AST-summarise → fix → validate → run tests → commit to a *new branch*. Never commit unverified or untested changes to main. The branch is the safety net.

---

## What an interviewer is really testing

- *"How does a code agent actually improve its output?"* → A closed loop with an objective verifier (tests/compiler). It feeds concrete failure output back into the next generation. The verifiability of code is what makes this work where text agents can't self-grade reliably.
- *"How do you safely run code an LLM wrote?"* → Subprocess sandbox with timeout and captured output; never `exec()` in-process; ideally resource/network limits and a container. Treat all generated code as hostile.
- *"How do you stop the loop from running forever / costing too much?"* → Bound on *both* iterations and dollars; track cumulative cost per run and abort. Detect non-improving loops (same failure repeating).
- *"Why use AST instead of string replacement to edit code?"* → AST gives you structural understanding and a parse-validity guarantee; string edits silently corrupt code and can't tell a function from a comment.

---

## Tradeoffs & gotchas

- **Sandbox escapes are real.** Subprocess + timeout is the baseline; for true isolation use containers with no network and resource caps. An LLM can be tricked into writing `os.system('rm -rf')`.
- **Test quality bounds the agent.** The agent is only as good as the tests it's graded against — weak tests → confidently wrong code that "passes." Garbage tests in, garbage code out.
- **Infinite/oscillating loops.** Cap iterations AND cost; detect repeated identical failures and bail.
- **Overfitting to tests.** An agent can hard-code outputs to pass specific tests rather than solve the problem. Hidden/held-out tests catch this.
- **Never auto-commit to main.** Branch, validate (AST), test, *then* a human (or a gate) merges. (Ties to Week 9 human-in-the-loop and Week 7 CI gates.)

---

## Self-test

<details><summary>1. Why do code agents work better than pure-text agents at self-improvement?</summary>
Code is objectively verifiable — you can run it and get unambiguous pass/fail feedback to feed back into the loop. Text has no equivalent ground-truth signal.</details>

<details><summary>2. How must you run LLM-generated code, and what must you never do?</summary>
In an isolated subprocess (ideally a container) with a timeout and captured output. Never exec() it in your own process. Treat it as hostile.</details>

<details><summary>3. Name both bounds on the fix loop and why both are needed.</summary>
max_iterations (stop endless retries) and max_cost_usd (stop unbounded spend). An impossible test could otherwise loop and bill forever.</details>

<details><summary>4. Why validate generated code with ast.parse() before running/committing?</summary>
It guarantees the code at least parses, preventing you from running or committing syntactically broken code — a cheap, decisive guard.</details>

---

**Labs:** `1` sandbox execution → `2` write→test→fix loop → `3` AST-aware editing → `4` git integration. App: `app.py` (paste a failing test, watch it pass).

**Next:** [Week 9 Primer](../9_human_in_the_loop/PRIMER.md) — keeping a human in control of autonomous agents.
