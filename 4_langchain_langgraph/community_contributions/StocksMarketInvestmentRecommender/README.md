# 🧩 LangGraph-Based Stocks Market Recommender

> This project was built using **LangGraph**, one of the agentic frameworks covered in the course.

This contribution showcases a full **agentic LangGraph system** for stock market analysis and investment recommendation, built during my participation in Ed’s **Agentic AI Course**.

It demonstrates how multiple **LangGraph-based agents** can collaborate within a **hierarchical, reasoning-driven flow**, powered by an infrastructure I built to simplify LangGraph usage.

---

## 🧠 Project Overview

The system is composed of two connected graphs:

- 🧩 **[LangGraphWrappers](https://github.com/Omer-Pinto/LangGraphWrappers)**  
  A lightweight DSL and infrastructure layer wrapping LangGraph primitives — making graph construction, node linking, model setup, and tool lifecycle management concise and clean.

- 💹 **[StocksMarketRecommender](https://github.com/Omer-Pinto/StocksMarketRecommender)**  
  A complete multi-agent, multi-graph project:
  - **Market Analyst Graph**: performs structured, tool-assisted financial analysis using Yahoo Finance MCP.  
  - **Agentic Stock Analyzer Graph**: orchestrates reasoning and controls when and how often to execute the subgraph.  
    It introduces an *agentic control loop*, where a manager node iteratively decides whether more information is needed before making investment decisions.

---

## 🗺️ LangGraph Flow Diagrams

### Market Analyst Graph
![Market Analyst Graph](https://raw.github.com/Omer-Pinto/StocksMarketRecommender/main/resources/market_analyst_graph.png)

### Agentic Flow Analyzer Graph
![Agentic Flow Analyzer Graph](https://raw.github.com/Omer-Pinto/StocksMarketRecommender/main/resources/agentic_flow_analyzer_graph.png)


---

## 🎯 What It Demonstrates

- **Agentic Control Flow** – The main graph autonomously decides when and how often to invoke analytical subgraphs.
- **Reusable Subgraphs** – The Market Analyst Graph is reusable and standalone.
- **Agentic decision loops** driven by state and router logic.  
- **Structured outputs** and typed agent communication via Pydantic.  
- Integration of **LangChain tools**, **MCP servers**, and **stateful agent collaboration**.
- **Structured State Management** - demonstrating alternative flow control using a dedicated `ControlMessage` and state detailed fields instead of long `messages` list.

---

## 🪄 Learn More

Full documentation, diagrams, and detailed explanations are available in:

- 🔗 [LangGraphWrappers README](https://github.com/Omer-Pinto/LangGraphWrappers/blob/main/README.md)  
- 🔗 [StocksMarketRecommender README](https://github.com/Omer-Pinto/StocksMarketRecommender/blob/main/README.md)

Each repo includes architecture descriptions, full flow breakdowns, and working examples.

---

## 🙏 Acknowledgments

Created as part of **Ed’s Agentic AI Course**.  
Thanks to **Ed** and the course community for the inspiration, teaching, and motivation to push LangGraph experimentation further.  
Maintained by **[Omer Pinto](https://github.com/Omer-Pinto)**.
