import os
import sqlite3
import logging
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

logging.getLogger("autogen").setLevel(logging.WARNING)

load_dotenv()

DB_PATH = "sample.db"


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            country TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product TEXT,
            amount REAL,
            order_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        DELETE FROM customers;
        DELETE FROM orders;

        INSERT INTO customers VALUES
            (1, 'Alice Wanjiru', 'alice@example.com', 'Kenya'),
            (2, 'Bob Kamau', 'bob@example.com', 'Kenya'),
            (3, 'Carol Fatuma', 'carol@example.com', 'Tanzania'),
            (4, 'David Muhoozi', 'david@example.com', 'Uganda'),
            (5, 'Abdi Juma', 'abdi@example.com', 'Tanzania');

        INSERT INTO orders VALUES
            (1, 1, 'Laptop', 1200.00, '2024-01-15'),
            (2, 1, 'Mouse', 25.00, '2024-02-10'),
            (3, 2, 'Keyboard', 75.00, '2024-01-20'),
            (4, 3, 'Monitor', 400.00, '2024-03-05'),
            (5, 4, 'Laptop', 1200.00, '2024-03-10'),
            (6, 4, 'Headphones', 150.00, '2024-03-12'),
            (7, 5, 'Webcam', 90.00, '2024-02-28'),
            (8, 2, 'Monitor', 400.00, '2024-04-01');
    """
    )
    conn.commit()
    conn.close()


def get_schema() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    schema = ""
    for (table,) in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        cols = ", ".join(f"{col[1]} {col[2]}" for col in columns)
        schema += f"Table: {table} ({cols})\n"
    conn.close()
    return schema


def run_query(sql: str) -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]
        conn.close()

        if not rows:
            return "No results found."

        col_widths = [
            max(len(str(h)), max(len(str(r[i])) for r in rows))
            for i, h in enumerate(headers)
        ]
        header_row = " | ".join(
            str(h).ljust(col_widths[i]) for i, h in enumerate(headers)
        )
        separator = "-+-".join("-" * w for w in col_widths)
        data_rows = [
            " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers)))
            for row in rows
        ]
        return "\n".join([header_row, separator] + data_rows)
    except Exception as e:
        return f"Error: {e}"


llm_config = {
    "model": "gpt-4o",
    "api_key": os.getenv("OPENAI_API_KEY"),
    "temperature": 0,
}

schema = get_schema()

sql_writer = AssistantAgent(
    name="sql_writer",
    system_message=f"""You are an expert SQL assistant working with a SQLite database.

Database schema:
{schema}

When the user asks a question, write a clean SQLite SQL query to answer it.
Return only the raw SQL query with no explanation, no markdown, no backticks.
""",
    llm_config=llm_config,
)

sql_reviewer = AssistantAgent(
    name="sql_reviewer",
    system_message=f"""You are a SQL reviewer. You check SQL queries for correctness and efficiency.

Database schema:
{schema}

When you receive a SQL query:
- If it looks correct, reply with just the word: APPROVED
- If it needs fixing, return the corrected SQL query only, no explanation.
""",
    llm_config=llm_config,
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=5,
    is_termination_msg=lambda msg: msg.get("content", "").strip() == "APPROVED",
    code_execution_config=False,
)

group_chat = GroupChat(
    agents=[user_proxy, sql_writer, sql_reviewer],
    messages=[],
    max_round=6,
    speaker_selection_method="round_robin",
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
)


def main():
    setup_database()
    print("SQL Query Agent")
    print("Database: customers, orders")
    print("Type 'exit' to quit\n")

    while True:
        question = input("Ask a question: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        user_proxy.initiate_chat(
            manager,
            message=question,
            clear_history=True,
        )

        select_keywords = ["SELECT", "WITH", "PRAGMA"]
        for msg in reversed(group_chat.messages):
            content = msg.get("content", "").strip()
            if not content or content == "APPROVED":
                continue
            if any(content.upper().startswith(kw) for kw in select_keywords):
                print("\nResult:\n")
                print(run_query(content))
                break
        print()


if __name__ == "__main__":
    main()
