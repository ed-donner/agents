# Week 2 Challenge Variant

This folder is an alternative version of the original implementation in `/2_openai/deep_research`.

## High-Level Changes

Compared with the original version, this variant introduces a more interactive and more agentic flow:

- A clarification step was added before research starts.
- The clarification happens as a chat-style Gradio experience, where the user answers 3 follow-up questions one at a time.
- The original query, the 3 clarification questions, and the 3 user answers are synthesized into a single refined query before research begins.
- The previous class-based `ResearchManager` workflow was replaced with a manager agent that orchestrates the research process by calling tool functions.
- The final research pipeline is now: clarify -> refine query -> manager agent -> plan searches -> perform searches -> write report -> print report.
- Printing is used instead of the original email-delivery step.

## Main Files In This Variant

- `clarification_agent.py`: generates the 3 clarification questions and synthesizes the refined query.
- `research_manager.py`: defines the tool-backed manager agent and the helper functions used before the main research run.
- `deep_research.py`: provides the Gradio chat interface and calls the manager agent after clarification is complete.
- `printer_agent.py`: replaces the original email output with plain-text printing.
- `poor_man_web_search.py`: provides a lightweight local search utility used by the search agent.

## Why Use `poor_man_web_search.py`

`poor_man_web_search.py` is a simple, low-cost alternative to `agent.WebSearchTool` for basic experiments and local development.

It is useful when:

- you want to avoid paid search APIs
- you only need lightweight search behavior
- you are prototyping and want a simple local-first setup

Tradeoff:

- it is cheaper and simpler, but generally less robust and less feature-rich than `agent.WebSearchTool`

## Note

Because `poor_man_web_search.py` relies on lightweight scraping/search behavior, it may be less reliable and may hit rate limits if overused.
