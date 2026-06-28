# SidekickAI

This is an overview of my **SidekickAI** project, available at the following link.

🔗 **GitHub Repository:**  
https://github.com/Jsrodrigue/sidekickAI

SidekickAI is a personal AI assistant designed to **enhance productivity and knowledge management** through persistent, structured conversations and isolated contexts.  
You can **create and use folder-based knowledge bases**, or **use the chat as a general assistant without selecting any folder**.

---

## Overview

SidekickAI introduces a **folder-based knowledge system** where each folder represents an independent workspace.  
At the same time, the system can be used **without any folder**, behaving like a standard AI assistant.

When folders are used:

- Each folder has its own dedicated chat
- Contexts are fully isolated (no cross-folder leakage)
- Conversations are persistent and resumable
- Multiple projects or topics can be handled in parallel

When no folder is selected:

- The assistant works in **general chat mode**
- No knowledge base or RAG is used
- The experience is lightweight and flexible

---

## Demo Video

Click the image below to watch a full demo of **SidekickAI** on YouTube:

[![SidekickAI Demo](https://img.youtube.com/vi/BiodhwA6oEg/0.jpg)](https://youtu.be/BiodhwA6oEg)

---

## Core Features

### 🧠 Context-Isolated Knowledge Bases
- Each folder represents an independent knowledge base
- Separate chat history per folder
- Persistent conversations per user and per folder
- No context mixing between projects
- Optional: folders are **not required** to use the system

### 🔍 Optional and Dynamic RAG
- RAG is implemented as **an optional tool**
- The agent decides when retrieval is useful
- Can be enabled or disabled at runtime
- When no folder is selected, the agent works without RAG

### 🧩 Modular Agentic Architecture
- Built with **LangGraph**
- Deterministic and controlled agent loop
- Tool usage is conditional and bounded
- Easy to extend with new nodes, tools, or agents

### 📁 Flexible Knowledge Indexing
- Semantic indexing per folder
- Independent configuration per knowledge base:
  - Chunk size
  - Chunk overlap
  - Retrieval count
- Indexing pipeline designed to support new file formats easily

### 🔐 User Authentication & Persistence
- User-based authentication
- Private conversations and settings
- Knowledge bases isolated per user

### 🛠️ Integrated Tooling
- Retrieval-Augmented Generation (RAG)
- File read/write/list tools
- Python execution
- Web search
- Wikipedia lookup
- LangGraph-based agent orchestration

---

## Models and AI Stack

- **Chat Model:** `gpt-4o-mini`  
  Selected to balance cost efficiency with strong reasoning and tool usage.
- **Embedding Model:** `text-embedding-ada-002`  
  Used for semantic indexing and document retrieval.
- **Frameworks:**
  - LangGraph for agent orchestration
  - LangChain ecosystem for retrieval, tools, and integrations

---

## Supported File Types for Indexing

Currently supported formats:
- PDF (`.pdf`)
- Markdown (`.md`)
- Plain text (`.txt`)
- Python source files (`.py`)

The architecture allows new file types to be added without changes to the core logic.

---

## RAG Design Philosophy

RAG is **not mandatory** in SidekickAI:

- It is used only if:
  - The tool is enabled
  - A knowledge base folder is selected
  - The agent determines retrieval is useful
- If RAG is disabled or no folder is selected:
  - The agent responds using only the LLM and other enabled tools

This design allows both **general-purpose assistance** and **knowledge-grounded interaction** within the same system.

---

## Usage Flow

1. Create an account
2. Log in to your workspace
3. (Optional) Create or select a knowledge base folder
4. Chat with SidekickAI inside the selected context or in general mode

---

## Knowledge Base Configuration

Each folder can be configured independently:

- **Chunk Size** – controls document splitting during indexing
- **Chunk Overlap** – improves context continuity
- **Retrieval Count** – number of documents retrieved per query

---

## LangGraph Architecture Overview

SidekickAI uses a **simple and extensible agent loop** built with LangGraph.

### Nodes

**Worker Node**
- Main LLM node with tools bound
- Dynamically builds the system prompt
- Decides whether tool usage is required

**Tool Node**
- Executes tool calls emitted by the worker
- Supports multiple tool calls per turn with safety limits

### Control Flow

1. START → Worker  
2. Worker:
   - Tool calls present → Tool Node
   - No tool calls → END  
3. Tools → Worker  
4. Worker → END when no further actions are required

### Key Design Decisions

- Tool usage is conditional and bounded
- Disabled tools are respected at runtime
- Memory is persisted per folder using a checkpointer
- RAG is treated as an optional tool
- Architecture is prepared for:
  - Additional nodes
  - Validation or guardrails
  - Multi-agent routing

---

## License

See the LICENSE file in the repository for details.
