# Langgraph - how to retrieve checkpoint_id(s) from the history and re-run the graph

### The importance of checkpoints:

Checkpoint is one of reason that I become a true believer of Langgraph. The other reason is abundant resources in Langchain community.

Agentic AI applications often involve multi-agent and multiple steps. Breakpoint help repeat isolated testing and cut down the cost.  If I have formating or wording issue in the send_email step in Deep Research project, I can just refine and test send_email alone and no need to repeat plan_search, perform_search and write_report and pay additional cost incurred.

### How to retrieve checkpoints:

In Langgraph, each step is a so-call StateSnapshot.  For example,

```
latest_snapshot = graph.get_state(config)
```

will get the latest snapshot

``StateSnapshot(values={'messages': [HumanMessage(content='search the exchange rate of usd to canadian and send a push notification to me', additional_kwargs={}, response_metadata={}, id='e692e5c0-d541-4427-bad3-11f3d4153bb6'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_Fby8bL918lXD4MxD5KyuouFZ', 'function': {'arguments': '{"__arg1":"current exchange rate USD to CAD"}', 'name': 'search'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 20, 'prompt_tokens': 103, 'total_tokens': 123, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_c4585b5b9c', 'id': 'chatcmpl-Cp0k7ZX4M2ZOXlRMwTgLFcLjoigAr', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run--438b47ed-e341-47d4-95e7-62f9dab88725-0', tool_calls=[{'name': 'search', 'args': {'__arg1': 'current exchange rate USD to CAD'}, 'id': 'call_Fby8bL918lXD4MxD5KyuouFZ', 'type': 'tool_call'}], usage_metadata={'input_tokens': 103, 'output_tokens': 20, 'total_tokens': 123, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}), ToolMessage(content='1.38 Canadian Dollar', name='search', id='4d0e2339-a060-4c5f-966d-26497fba2c70', tool_call_id='call_Fby8bL918lXD4MxD5KyuouFZ'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_a4K74sBrvNkxvCweY7xBQ4uh', 'function': {'arguments': '{"__arg1":"The current exchange rate is 1 USD = 1.38 CAD."}', 'name': 'send_push_notification'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 31, 'prompt_tokens': 135, 'total_tokens': 166, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_c4585b5b9c', 'id': 'chatcmpl-Cp0k96XL94rOHYkqjE6ao63W5cthB', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run--ba0bc188-a302-438e-9072-0b2750bbc17a-0', tool_calls=[{'name': 'send_push_notification', 'args': {'__arg1': 'The current exchange rate is 1 USD = 1.38 CAD.'}, 'id': 'call_a4K74sBrvNkxvCweY7xBQ4uh', 'type': 'tool_call'}], usage_metadata={'input_tokens': 135, 'output_tokens': 31, 'total_tokens': 166, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}), ToolMessage(content='null', name='send_push_notification', id='06f468dc-43d1-4149-9c57-baaa220390a0', tool_call_id='call_a4K74sBrvNkxvCweY7xBQ4uh'), AIMessage(content="The current exchange rate is 1 USD = 1.38 CAD, and I've sent you a push notification with this information.", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 27, 'prompt_tokens': 176, 'total_tokens': 203, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_c4585b5b9c', 'id': 'chatcmpl-Cp0kCTlet63rpwA49f7MfQJMcowjJ', 'service_tier': 'default', 'finish_reason': 'stop', 'logprobs': None}, id='run--3e302fb1-349e-4465-bff8-9279e59c94ec-0', usage_metadata={'input_tokens': 176, 'output_tokens': 27, 'total_tokens': 203, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}, next=(), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0ddfc5-39a6-6116-8005-423c2c2a09e6'}}, metadata={'source': 'loop', 'step': 5, 'parents': {}}, created_at='2025-12-20T23:33:45.260864+00:00', parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1f0ddfc5-2316-6d24-8004-df7b9978987f'}}, tasks=(), interrupts=())``

We can get checkpoint by

```
latest_snapshot.config['configurable']['checkpoint_id']
```

and the output will be

`'1f0ddfc5-39a6-6116-8005-423c2c2a09e6'`

However, we need to know the whole history of the graph invocation that involves multiple StateSnapshots. `graph.get_state_history` will do the trick.

```
list(graph.get_state_history(config))
```

We also need to know the context of each StateSnapshot.  The followings are the dump of 2_lab MemorySaver example.

---

checkpoint_id= 1f0ddfc4-f907-63b2-bfff-cc8e490d26f8
next= ('__start__',)

---

checkpoint_id= 1f0ddfc4-f909-696e-8000-ce0f54506b34, message_type= "HumanMessage", message_content= "search the exchange rate of usd to canadian and send a push notification to me"
next= ('chatbot',)

---

checkpoint_id= 1f0ddfc5-08f2-69ac-8001-5ecf936ca23d, message_type= "AIMessage", tool_call:, name= "search", args= "current exchange rate USD to CAD",
finish_reason= "tool_calls" next= ('tools',)

---

checkpoint_id= 1f0ddfc5-1149-6a42-8002-36424b587855, message_type= "ToolMessage", tool_name= "search", message_content= "1.38 Canadian Dollar"
next= ('chatbot',)

---

checkpoint_id= 1f0ddfc5-213c-6148-8003-0e4a36a7839c, message_type= "AIMessage", tool_call:, name= "send_push_notification", args= "The current exchange rate is 1 USD = 1.38 CAD."
finish_reason= "tool_calls" next= ('tools',)

---

checkpoint_id= 1f0ddfc5-2316-6d24-8004-df7b9978987f, message_type= "ToolMessage", tool_name= "send_push_notification", message_content= "null"
next= ('chatbot',)

---

checkpoint_id= 1f0ddfc5-39a6-6116-8005-423c2c2a09e6 message_type= AIMessage, finish_reason= "stop" next= ()

---

Please notice a couple of things:
`graph.get_state_history` is in the reverse order with the latest first.
Each StateSnapshot has accumulated Messages. You do need to retrieve the latest Message.
One AI Message can have multiple tool_calls. AIMessage is the engine that has the instructions of tool calls. The code that  dump the history and relevant information is in the Juypter Notebook.

### How to re-run with a checkpoint.

If you want to re-run `send_push_notification` only, you need to set the checkpoint to the AIMessage prior to that ToolMessage because AIMessage has the instruction of the ToolMessage.

```
config = {"configurable": {"thread_id": "1", "checkpoint_id": "1f0ddfc5-213c-6148-8003-0e4a36a7839c"}}
graph.invoke(None, config=config)
```

If you want to re-run the whole graph flow, you can either set the checkpoint to the HumanMessage which is the second one.

```
config = {"configurable": {"thread_id": "1", "checkpoint_id": "1f0ddfc4-f909-696e-8000-ce0f54506b34"}}
graph.invoke(None, config=config)
```

Or you can set the checkpoint to the very beginning.

```
config = {"configurable": {"thread_id": "1", "checkpoint_id": "1f0ddfc4-f907-63b2-bfff-cc8e490d26f8"}}
graph.invoke(None, config=config)
```

### Github Codes:

https://github.com/threecuptea/agents
