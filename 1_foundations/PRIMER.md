# Week 1 Primer — Foundations: LLMs, Tools, and the Agent Loop

> **Read this before the labs.** The labs teach you to *type* the code. This primer
> gives you the mental model the code is an instance of — the thing an interviewer
> actually probes. 15 minutes here makes the 4 labs click.

---

## The one mental model

An **LLM is a stateless function**: `text in → text out`. It has no memory, no ability to act in the world, and no knowledge of anything after its training cutoff. Everything else in this entire course is scaffolding around that one limited function to make it *useful*.

An **agent** is what you get when you let the LLM's output *control a loop*:

```
        ┌─────────────────────────────────────────────┐
        │                                             │
        ▼                                             │
  ┌───────────┐   wants to       ┌──────────────┐     │
  │   LLM     │── call a tool ──▶│ run the tool │─────┘
  │  (brain)  │                  │ (hands)      │  feed result back
  └───────────┘                  └──────────────┘
        │
        │ no tool call → done
        ▼
     final answer
```

That loop — *call the LLM, if it asked for a tool run the tool and loop, else stop* — is **the agent loop**. Every framework in Weeks 2–6 (OpenAI SDK, CrewAI, LangGraph, AutoGen, MCP) is a different ergonomic wrapper around this exact loop. If you understand it from first principles now, the frameworks become "oh, this is just the loop, with nicer syntax."

---

## The four things you bolt onto the stateless function

| Limitation of a raw LLM | What fixes it | Lab |
|--------------------------|---------------|-----|
| No memory between calls | You resend the whole conversation every time (`messages` list) | 1 |
| Can't act in the world | **Tools** — functions the LLM can ask you to run | 4 |
| Doesn't know your data | **Context injection** — paste relevant text into the prompt | 3 |
| Output can't be trusted blindly | **Structured output + evaluation** — Pydantic schema, LLM-as-judge, retry | 2, 3 |

Internalise this table. Nearly every "advanced" agent technique later is a more sophisticated version of one of these four moves.

---

## Key concepts, precisely

**The message list.** A chat call takes a list of `{role, content}` dicts: `system` (the standing instructions/persona), `user`, `assistant`. The model is stateless, so *you* maintain history by appending each turn and resending the whole list. "Conversation memory" is just an ever-growing list you carry. (This is also why long chats cost more — you pay for the whole history on every turn.)

**Tools / function calling.** You describe a function to the LLM as a JSON schema (name, description, parameters). The LLM can't *run* code — it returns a structured request *"please call `get_weather` with `{city: 'Paris'}`"*. Your code runs the real function and feeds the result back. The LLM never touches your system; it only ever emits text that *describes* an action.

**The agent loop.** `while the LLM keeps asking for tools: run them, append results, call again. Stop when it returns a plain answer.` That `while not done` loop is the entire definition of "agent." Memorise that you can write it in ~15 lines with no framework — Lab 4 and `5_extra.ipynb` do exactly that.

**LLM-as-judge.** Use a second LLM call to *grade* a first one (rank candidates, score quality, decide pass/fail). It's the cheapest evaluation method and shows up everywhere — but it has known biases (length, position, self-preference) you must control for. (Week 7 / Week 9 go deep.)

**Structured outputs.** Force the model to return JSON matching a Pydantic schema. This turns an unpredictable text blob into a typed object your code can branch on reliably. It's the bridge between "the LLM said something" and "my program can act on it."

---

## What an interviewer is really testing

When they ask *"what is an agent?"* the weak answer is "an AI that does tasks." The strong answer:

> "An agent is an LLM placed in a loop where its output controls which tools get
> called and when, iterating until a goal is reached. The LLM is the controller;
> tools are how it observes and acts. The core is a `while not done` loop — the
> frameworks just make it ergonomic."

When they ask *"how does function calling actually work — does the model run the code?"* — the test is whether you know the model **never executes anything**. It emits a structured request; your runtime executes and returns the result. Getting this wrong signals you've only used agents as a black box.

---

## Tradeoffs & gotchas

- **Conversation history grows unbounded.** Every turn resends everything → cost and latency climb, and you eventually hit the context window. Real systems truncate, summarise, or use memory stores (Week 3, Week 4 checkpointing).
- **Tool descriptions are prompt engineering.** The LLM decides whether/how to call a tool purely from its name + description. Vague descriptions = wrong or missed tool calls. Treat them as carefully as system prompts.
- **More model ≠ better.** Lab 1 compares nano vs mini. The senior instinct is to pick the *cheapest model that passes your eval*, not the biggest (formalised in Week 7 Lab 9).
- **Never trust raw output for control flow.** Branch on *structured* output (Pydantic), not on string-matching free text.

---

## Self-test (answer from memory, then expand)

<details>
<summary>1. Why do we resend the entire conversation on every API call?</summary>

Because the LLM is **stateless** — it retains nothing between calls. The `messages` list *is* the memory; the model only "remembers" what you put in front of it this turn.
</details>

<details>
<summary>2. When the LLM "calls a tool," what actually executes the function?</summary>

**Your code does.** The LLM only returns a structured request naming the tool and arguments. Your runtime dispatches to the real function, runs it, and appends the result to the message list for the next call. The model never runs code.
</details>

<details>
<summary>3. Write the agent loop in pseudocode.</summary>

```
messages = [system, user]
while True:
    response = llm(messages)
    if response.tool_calls:
        for call in response.tool_calls:
            result = run_tool(call.name, call.args)
            messages.append(tool_result(result))
        messages.append(response)   # keep the assistant's tool request too
    else:
        return response.content      # plain answer → done
```
</details>

<details>
<summary>4. Name the four limitations of a raw LLM and the fix for each.</summary>

No memory → resend history. Can't act → tools. Doesn't know your data → context injection. Untrustworthy output → structured output + evaluation/retry.
</details>

---

## Then do the labs

`1_lab1` (API calls) → `2_lab2` (multi-provider + judge) → `3_lab3` (context + Gradio + eval) → `4_lab4` (tools + the loop) → `5_extra` (loop deep-dive). The `app.py` capstone wires all four moves into one chatbot.

**Next:** [Week 2 Primer](../2_openai/PRIMER.md) — the same loop, now wrapped by a real SDK.
