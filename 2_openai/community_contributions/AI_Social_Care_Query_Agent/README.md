## 🧑‍⚕️ AI-SocialCare-Query-Agent

An AI-powered query assistant that translates natural language questions into SQL queries and runs them against a synthetic Social Care database.
This project demonstrates how AI can help managers and analysts quickly explore key performance indicators (KPIs) in adult social care.

🚀 Features

🗂️ SQLite synthetic database with realistic UK-style social care data (Clients, Assessments, Services, Outcomes).

🤖 AI Query Agent powered by OpenAI (gpt-4o-mini), translating natural language → SQL → results.

🛡️ Safe execution – only SELECT queries are allowed.

📊 Formatted results – outputs in clean tables with explanations.

🔍 Trace logging – captures full chain-of-thought (NL → SQL → result) for transparency and audit.



## 📖 Project Overview

This project demonstrates how to build an AI-powered SQL query assistant using the OpenAI SDK, SQLite, and custom tools. The assistant allows users to type natural language queries, which are then translated into valid SQL, executed against a local database, and returned in a structured format.

## ⚙️ Architecture & Flow

### Agent (AI Reasoning Core)

The agent acts as the "brain" of the system.It receives user prompts, reasons about the intent, and decides whether to directly answer or invoke a tool.
The system prompt and schema were defined at initialization to control its behavior.

### Runner (Execution Engine)
The runner is the orchestrator.
It manages each step of the agent’s reasoning process, calling tools when required.
It ensures that user input, agent reasoning, tool outputs, and final responses flow smoothly.
Think of it as the "conductor of the orchestra."

### Tracer (Debugging & Transparency Layer)

The tracer records every step of the agent’s reasoning.

It captures:
The agent’s thought process (chain-of-thought).
When and how tools are called.
Raw SQL queries generated.
Responses from the database.
This makes debugging much easier when the assistant generates invalid queries or unexpected results.

### Tools (Functional Capabilities)

Tools are specialized Python functions that the agent can call.
Each tool has:
A name (how the agent knows it).
A description (when to use it).
A Python function (actual logic).

Example in the project:
execute_sql(query: str) → Runs SQL against SQLite and returns results.
Tools expand the agent’s power — instead of doing everything in text, it can call functions.

### Decorator Usage (@tool)

This tool was used (from the OpenAI SDK) to register a function as a tool.
This automatically makes the function available to the agent, with metadata (name & description).


## 🔄 End-to-End Flow

User Input → Natural language question.
Agent → Interprets input, plans next step.

Runner → Passes control to the correct tool (if needed).

Tool → Executes SQL, retrieves data.

Tracer → Logs the whole interaction.

Agent → Crafts final natural-language answer.

User Output → Clean results (tables, summaries, etc.).



## Tech Stack

Python

SQLite (for database)

OpenAI SDK (for AI query translation & structured outputs)

OpenAI Tracing Tools (AgentTracer, Runner for monitoring and execution)

dotenv (for managing API keys securely)




## 🏗️ Database Schema

The synthetic database contains 4 core tables:
clients – demographics & postcode

assessments – assessment history (type, assessor, date)

services – allocated care services with provider info

outcomes – service outcomes (Independence, Safety, etc.)

Each table links via client_id for relational queries.




## ⚙️ Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/tosincarik/AI-SocialCare-Query-Agent.git
cd AI-SocialCare-Query-Agent
```


### 2. Create environment with uv

```bash
uv venv
source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)
uv pip install -r requirements.txt
```

### 3. Environment variables

Create a .env file:

```python
OPENAI_API_KEY=your_api_key_here
```

### 4. Run database setup

The script automatically creates tables and populates with Faker-generated data

```bash
python scripts/setup_db.py
```

### 5. Run the agent

Launch an example query:

message = "List the adults aged over 20 years with their service outcome"
result = await Runner.run(resultagent, message)
print(result.final_output)

## 🧪 Example Query

User:
Show me the total number of clients by gender

Agent Output:
{
  "sql": "SELECT gender, COUNT(*) as total_clients FROM clients GROUP BY gender;",
  "explanation": "This query counts the number of clients in each gender category."
}


Result (formatted):
gender	total_clients
Male	26
Female	24




## Usage

Type a natural language query (e.g., "Show me the average age of clients with pending referrals")
Agent translates query → SQL → Executes → Returns structured output
Use Agent Tracer to monitor steps, debug, and view logs

Example Queries
"List the top 5 clients by number of assessments"
"What is the average time between referral and assessment?"
"Show a summary of services provided by category"


## 📜 License

MIT License – feel free to use, modify, and share.