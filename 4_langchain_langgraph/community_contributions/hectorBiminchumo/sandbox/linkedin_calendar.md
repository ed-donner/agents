# LinkedIn Content Calendar — Next 5 Weekdays

## 2026-10-21 (Wednesday)
**Topic:** The building blocks of an agent: LLM, tools, memory
**Hook:** I started with the simplest useful agent stack I could build.
**Draft:** This week in my AI engineering course, I went back to basics: an agent is really an LLM plus tools plus memory. I built a simple agent with search, Wikipedia, and a push notification tool, and that made the idea click for me. The LLM decided what to do, the tools extended what it could do, and memory gave it continuity. Practical takeaway: if your agent feels complicated, strip it down until you can explain each block in one sentence.
**Hashtags:** #AIAgents #LLM #PromptEngineering
**Source:** https://www.anthropic.com/engineering/building-effective-agents

## 2026-10-22 (Thursday)
**Topic:** LangGraph: orchestration with state, nodes and edges
**Hook:** Drawing my agent as a graph made the workflow finally feel concrete.
**Draft:** I spent time mapping my agent into LangGraph, and I drew the graph as a diagram before I read through its nodes and edges. Seeing the state move from step to step helped me understand orchestration in a much clearer way than a linear prompt ever did. Practical takeaway: when an agent has multiple steps, draw the state machine first so you can see where control actually moves.
**Hashtags:** #LangGraph #AIEngineering #StatefulAgents
**Source:** https://www.langchain.com/blog/building-a-stateful-agent-with-langgraph

## 2026-10-23 (Friday)
**Topic:** create_agent and middleware: planning, guardrails, human approval
**Hook:** The best guardrail I learned this week was simple: stop and ask.
**Draft:** I explored create_agent and middleware, especially how planning and guardrails can keep an agent safe. In my course work, I made my agent pause for my approval before it could write a file, and that human checkpoint changed how I think about control. It felt less like automation for its own sake and more like supervised execution. Practical takeaway: for high-impact actions, build in a pause before the tool runs.
**Hashtags:** #Middleware #Guardrails #HumanInTheLoop
**Source:** https://blog.langchain.com/agent-middleware-human-in-the-loop

## 2026-10-26 (Monday)
**Topic:** MCP servers: a real browser and a filesystem
**Hook:** I learned that live tools can reveal messy real-world behavior fast.
**Draft:** This week I used MCP servers to connect an agent to a real browser and a filesystem. I asked my agent to search flights on Expedia; it paused so I could log in myself, and I noticed it searched from Lima instead of New York because the site had prefilled the origin. That was a useful reminder that browser-based agents inherit whatever the page is already doing. Practical takeaway: always inspect the actual page state before trusting the first result.
**Hashtags:** #MCP #BrowserAutomation #AIAgents
**Source:** https://www.anthropic.com/news/model-context-protocol

## 2026-10-27 (Tuesday)
**Topic:** The Sidekick: a worker with an evaluator loop
**Hook:** My first pass at this calendar needed a second pass.
**Draft:** I used Sidekick to help plan this very calendar, and the first run reused sources and sounded generic. That was the moment the worker-evaluator loop made sense to me: one pass creates, another pass judges, and the system improves before it ships. I could see why evaluation is part of the workflow, not a bonus at the end. Practical takeaway: if you want better agent output, give the agent a reviewer that can push it to revise.
**Hashtags:** #Sidekick #Evaluation #AgenticAI
**Source:** https://www.builder.io/blog/sidekick
