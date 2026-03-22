# SQL Query Agent

A multi-agent system built with AutoGen that translates natural language questions into SQL queries and runs them against a local SQLite database.

## How it works

Three agents collaborate in a group chat:

- `sql_writer` — converts the user's question into a SQLite query
- `sql_reviewer` — checks the query and either approves it or returns a corrected version
- `user_proxy` — extracts the final query from the chat history and executes it

## Setup

```bash
uv add pyautogen openai python-dotenv
```

Create a `.env` file:

```
OPENAI_API_KEY=sk-...
```

## Running

```bash
python sql_query_agent.py
```

```
Ask a question: who are the top customers by total spend?
```

## Database

The agent comes with a sample SQLite database containing two tables:

- `customers` — id, name, email, country
- `orders` — id, customer_id, product, amount, order_date