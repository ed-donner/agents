# Community Contributions — Best of

This index highlights the most instructive community submissions across all weeks. Each entry explains *why* it's worth reading — not just what it does.

---

## Week 1 — Foundations

| Notebook | Author | Why it's interesting |
|----------|--------|----------------------|
| [Parallelization pattern](1_foundations/community_contributions/2_lab2_Kaushik_Parallelization.ipynb) | Kaushik | Clean fan-out pattern: one orchestrator spawns N workers in parallel and merges results. The canonical async gather pattern for agents. |
| [Routing workflow](1_foundations/community_contributions/2_lab2_Routing_Workflow.ipynb) | Community | Implements a router that classifies the query and dispatches to a specialist agent. Foundational pattern for multi-domain agents. |
| [ReAct pattern](1_foundations/community_contributions/2_lab2_ReAct_Pattern.ipynb) | Community | Explicit Reason → Act → Observe loop coded by hand. Reading this makes LangGraph's ToolNode feel obvious — good prereader. |
| [Reflection pattern](1_foundations/community_contributions/2_lab2_reflection_pattern.ipynb) | Community | Agent reviews its own output and rewrites it. Simpler version of the evaluator-retry loop in Week 4 Lab 4. |
| [Multi-evaluation criteria](1_foundations/community_contributions/2_lab2_multi-evaluation-criteria.ipynb) | Community | LLM-as-judge with multiple rubric dimensions (accuracy, clarity, tone). Extends the single-score judge into a structured scorecard. |
| [Chain-of-Thought exercise](1_foundations/community_contributions/2_lab2_exercise_BrettSanders_ChainOfThought.ipynb) | Brett Sanders | Side-by-side comparison of raw vs CoT prompting on reasoning tasks. Nicely illustrates why CoT matters before you hit Week 7. |
| [Gemini-based foundations](1_foundations/community_contributions/1_foundations_using_gemini/) | Community | Full Week 1 re-implementation using the Gemini API. Useful reference if you want to run the course with Google's models instead of OpenAI. |
| [Groq + LLaMA foundations](1_foundations/community_contributions/1_lab1_groq_llama.ipynb) | Community | Shows how to swap OpenAI for Groq's free-tier LLaMA endpoint. Cost: $0. Good for learners watching their API spend. |

---

## Week 2 — OpenAI Agents SDK

| Notebook | Author | Why it's interesting |
|----------|--------|----------------------|
| [Deep research with clarifying questions](2_openai/community_contributions/Deep_Research_with_clarifying_questions_and_rate_limiting/) | Community | Extends the Lab 4 deep research pipeline with an initial clarification loop and per-user rate limiting. More production-realistic than the base lab. |
| [Deep research Q&A](2_openai/community_contributions/deep_research_qa/) | Community | Turns the research output into an interactive Q&A — the agent can answer follow-up questions about the report it just wrote. |
| [Code learning assistant](2_openai/community_contributions/code_learning_assistant/) | Community | Multi-agent system where a planner, coder, and reviewer collaborate. Shows the handoff pattern applied to a real engineering workflow. |
| [Agent manager refactor](2_openai/community_contributions/agent_manager_refactor/) | Community | Clean separation of agent configuration from runner logic. Good architectural pattern for keeping agent codebases maintainable. |

---

## Week 3 — CrewAI

| Notebook / Project | Author | Why it's interesting |
|--------------------|--------|----------------------|
| [Stock picker advance](3_crew/community_contributions/stock-picker-advance/) | Community | Extends the course's stock picker with additional research agents and a more structured output schema. Shows how to scale up a CrewAI project. |
| [Trip daily planner](3_crew/community_contributions/trip_daily_planner/) | Community | Day-by-day itinerary planner with budget tracking. Good example of CrewAI's sequential process feeding structured output between tasks. |
| [Conversational debate](3_crew/community_contributions/conversational-debate/) | Community | Two CrewAI agents argue opposite sides of a topic, then a judge summarises. A clean demo of multi-agent turn-taking. |

---

## Week 4 — LangGraph

| Notebook / Project | Author | Why it's interesting |
|--------------------|--------|----------------------|
| [Patch to PR pipeline](4_langgraph/community_contributions/patch_to_pr/) | Community | End-to-end: LangGraph agent reads a bug description, writes a code patch, and opens a GitHub PR. High-value real-world workflow. |
| [Repo onboarding sidekick](4_langgraph/community_contributions/repo_onboarding_sidekick/) | Community | Agent that reads a codebase and generates an onboarding guide. Good use of Playwright tools + evaluator pattern together. |
| [Transcript summarizer](4_langgraph/community_contributions/transcript_summarizer/) | Community | Chunks long meeting transcripts, summarises each chunk, then synthesises a final summary. Shows how to handle context-window limits gracefully. |
| [Sidekick with planner](4_langgraph/community_contributions/ugomichael33/sidekick_with_planner/) | ugomichael33 | Adds a dedicated planning node before the worker node. The planner breaks the task into subtasks; the worker executes them one by one. |
| [HuggingFace Docker deploy](4_langgraph/community_contributions/sidekick_hf_docker_chromium_deploy/) | Community | Full deployment pipeline: builds a Docker image, runs Chromium headlessly, and deploys the Sidekick to HuggingFace Spaces. Bridges Lab 4 to production. |

---

## Week 5 — AutoGen

| Notebook / Project | Author | Why it's interesting |
|--------------------|--------|----------------------|
| [AgentChat team email](5_autogen/community_contributions/ugomichael33/week5_agentchat_team_email/) | ugomichael33 | Multi-agent email campaign: planner + writer + reviewer team, output sent via SendGrid. Shows Week 5 + Week 2 concepts combined. |

---

## Week 6 — MCP

| Notebook / Project | Author | Why it's interesting |
|--------------------|--------|----------------------|
| [Revised MCP](6_mcp/community_contributions/Revised_MCP/) | Community | Cleaner async context manager usage for MCP servers, addressing some of the boilerplate in the base labs. Good pattern reference. |
| [Emotion and MCP](6_mcp/community_contributions/emotion_and_mcp/) | Community | MCP server that exposes sentiment analysis as a tool. Interesting example of wrapping an ML model as an MCP endpoint. |
| [Emmy video processor](6_mcp/community_contributions/emmy_video_processor/) | Community | MCP server that processes video files and exposes transcription/summary tools. Shows MCP isn't just for web APIs. |

---

## How to contribute

Want to add your own notebook? Open a PR against the main branch:

1. Put your notebook in the appropriate `community_contributions/` folder
2. Add a `requirements.txt` listing your extra dependencies
3. Clear all cell outputs before committing (`Kernel → Restart & Clear Output`)
4. Add a brief description at the top of your notebook explaining what it does and why

Contributions that teach a new pattern, integrate a new tool, or show a real-world application get the most attention.
