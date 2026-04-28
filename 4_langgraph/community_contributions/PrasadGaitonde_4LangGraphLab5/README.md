# Intelligent Data Analysis Agent

A LangGraph-based multi-agent system that enables non-technical users to query databases using plain English.

## Architecture: Plan-Do-Check Loop

Instead of attempting to generate perfect SQL in one shot (Text2SQL), this agent uses a cyclical, self-correcting workflow that mimics how human analysts work:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. CLARIFIER: Ask 3 clarifying questions                       │
│     - Which tables are relevant?                                │
│     - What time period?                                         │
│     - What format/grouping?                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. PLANNER: Create analysis plan                               │
│     - Identify target tables                                    │
│     - Determine join strategy                                   │
│     - List required columns                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. QUERY WRITER: Generate SQL                                  │
│     - Write SELECT query based on plan                          │
│     - Include proper JOINs and filters                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. QUERY EXECUTOR: Run query                                   │
│     - Execute SQL safely (SELECT only)                          │
│     - Return results or error                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. QUERY CHECKER: Validate results                             │
│     - Check for errors                                          │
│     - Verify results match request                              │
│     - If FAILED → back to QUERY WRITER with feedback            │
│     - If PASSED → continue                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. OUTPUT FORMATTER: Present results                           │
│     - Format as readable table                                  │
│     - Show SQL used (transparency)                              │
│     - Include analysis notes                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **3 Clarifying Questions**: Before analysis, the agent asks targeted questions to understand your needs
- **Multi-Agent Architecture**: Specialized agents for planning, writing, executing, and checking
- **Self-Correcting Loop**: Query Checker validates results and requests rewrites if needed
- **SQL Memory**: Persistent storage for conversation history and query audit trail
- **Safe Execution**: Only SELECT queries allowed, with row limits

## Project Structure

```
4_langgraph/
├── app.py                    # Gradio UI
├── sidekick.py               # Main agent orchestration
├── sql_memory.py             # SQLite-based persistent memory
├── config.py                 # Configuration settings
├── init_sample_db.py         # Initialize sample database
├── requirements.txt          # Python dependencies
├── nodes/
│   ├── clarifier.py          # 3 questions generator
│   ├── planner.py            # Analysis planner
│   ├── query_writer.py       # SQL generator
│   ├── query_executor.py     # Query executor
│   ├── query_checker.py      # Result validator
│   └── output_formatter.py   # Output formatter
├── tools/
│   └── database_tools.py     # Database connection & tools
└── data/
    ├── analysis.db           # Sample SQLite database
    └── agent_memory.db       # Conversation/query history
```

## Quick Start

1. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   # Create .env file with:
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Initialize sample database**:
   ```bash
   uv run init_sample_db.py
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Try example queries**:
   - "Show me total sales by region"
   - "Which products have the highest stock?"
   - "Find customers who placed orders in January"
   - "What's the average order value per customer?"

## Example Session

```
User: Show me total sales by region

Agent (Clarifier): Before I can analyze your data request, I need some clarification:
1. Do you want sales totals, order counts, or both?
2. Should I include pending orders or only completed ones?
3. What time period should I analyze (all time, specific months)?

User: Total sales amounts, only completed orders, for Q1 2025

Agent (Planner): Analysis Plan:
Steps:
1. Filter orders for Q1 2025 (Jan-Mar)
2. Join orders with customers for region
3. Filter by status = 'completed'
4. Group by region and sum total_amount

Agent (Query Writer): Generated SQL:
SELECT c.region, SUM(o.total_amount) as total_sales
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
  AND o.order_date BETWEEN '2025-01-01' AND '2025-03-31'
GROUP BY c.region

Agent (Query Checker): Query Validation: PASSED

Agent (Output Formatter):
## Analysis Results
Status: Completed Successfully
Rows Returned: 4

## Results
region    total_sales
North         2799.65
South          729.92
East          2199.79
West           459.96
```

## Configuration

Edit `config.py` to customize:

- `DATABASE_PATH`: Path to your SQLite database
- `MEMORY_DB_PATH`: Path to conversation history database
- `MAX_QUERY_REWRITE_ATTEMPTS`: Max rewrite attempts before giving up (default: 3)
- `CLARIFYING_QUESTION_COUNT`: Number of clarifying questions (default: 3)
- `MAX_ROWS_RETURNED`: Maximum rows to return (default: 100)

## Memory Features

The SQL memory system (`sql_memory.py`) provides:

- **Session tracking**: Each analysis session is recorded
- **Conversation history**: Full message history per session
- **Query audit trail**: All generated queries with results
- **User preferences**: Learn user preferences over time
- **Analysis plans**: Store generated plans for reference

## Safety

- Only SELECT queries are executed
- Queries containing DROP, DELETE, TRUNCATE, ALTER, INSERT, UPDATE are blocked
- Result limits prevent memory exhaustion
- Query timeout prevents long-running queries

## License

MIT
