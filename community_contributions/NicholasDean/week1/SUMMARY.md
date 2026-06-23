# Week 1 — Foundations (agentic patterns, no framework)

First week of the agentic course: build agents from raw LLM calls — no framework yet.

- **One LLM call:** `OpenAI().chat.completions.create(model, messages)`; `gpt-4.1-nano`/`mini`
  are dirt cheap for experimenting.
- **Many providers, one client:** Anthropic, Gemini, DeepSeek, Groq and local Ollama are all
  OpenAI-compatible — same `OpenAI` class, just swap `base_url` + key.
- **Agentic workflow patterns** (from Anthropic's *Building Effective Agents*):
  - *Prompt chaining* — feed one call's output into the next (business idea → pain point → solution).
  - *Evaluator–optimizer* — one model answers, another grades it (Pydantic `is_acceptable`/`feedback`);
    rerun with the feedback if rejected.
  - *LLM-as-judge / ensemble* — ask N models the same question, have a judge rank them.
- **Tool use (the heart of an agent):** describe Python functions as JSON, pass `tools=` to the call;
  when `finish_reason=="tool_calls"`, run the function and loop until the model is done.
- **Pushover** sends a phone push from a tool (e.g. "someone left their email").
- Deploy a Gradio app to **HuggingFace Spaces** with `uv run gradio deploy`.

**Built:** `career_conversation.py` — a minimal "talk to Nicholas" agent. Reads a short bio,
answers as me, and uses two tools (record an interested visitor's email; record an unanswerable
question) that push to my phone. The week-1 agent loop in ~50 lines, no framework.

## Distilled learning

**ELI5:** An "agent" here is just an LLM you (a) give a job to in the system prompt and (b) hand a
few Python functions it's allowed to call. You loop: ask the model, and if it says "call this
function," you run it and feed the result back — repeat until it answers. That tool-calling loop is
the whole trick; the frameworks in later weeks just wrap it.

```python
while True:
    r = openai.chat.completions.create(model, messages, tools=TOOLS)
    if r.choices[0].finish_reason != "tool_calls":
        return r.choices[0].message.content        # model is done → final answer
    messages.append(r.choices[0].message)
    for call in r.choices[0].message.tool_calls:    # model asked for a tool → run it, append result
        result = globals()[call.function.name](**json.loads(call.function.arguments))
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
```
