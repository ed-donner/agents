# LLM orchestration run (`llm.py`)

`llm.py` uses LangChain `create_agent` to orchestrate a **main agent** that calls tools and a nested **apparel LLM subagent**. Weather and population are plain `@tool` functions. Packing advice is delegated: the main agent’s `apparel_agent` tool builds a second agent (with `suggest_suitable_clothes`) and `invoke`s it. `MemorySaver` plus a shared `thread_id` in `config` is the checkpointer so the second question (“what is the population of this city?”) still knows the city is Rome. Middleware (`@wrap_tool_call`) logs each tool vs subagent call. The structured result is a `CityReport`.

```
python llm.py

Intercepting the tool call...
[middleware] calling main agent tool:  get_weather with {'city': 'Rome'}.
Intercepting the tool call...
[middleware] calling main agent tool:  get_population with {'city': 'Rome'}.
Intercepting the tool call...
[middleware] calling subagent tool:  apparel_agent with {'city': 'Rome'}.
city='Rome' weather='rainy, 12 degrees' population='6m' clothes="For Rome, it's recommended to wear casual clothes and include a raincoat."
Deserializing unregistered type __main__.CityReport from checkpoint. This will be blocked in a future version. Set LANGGRAPH_STRICT_MSGPACK=true to block now, or add to allowed_msgpack_modules to allow explicitly: [('__main__', 'CityReport')]
city='Rome' weather='rainy, 12 degrees' population='6m' clothes="For Rome, it's recommended to wear casual clothes and include a raincoat."
```

The checkpoint warning on the second turn is LangGraph loading `CityReport` from memory; it does not stop the run. Both turns print the same structured report because the checkpointer kept Rome in the thread.
