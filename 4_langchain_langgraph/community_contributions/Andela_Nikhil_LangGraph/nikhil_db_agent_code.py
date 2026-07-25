from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
import requests
import gradio as gr

nikhil_llm = init_chat_model("openai:gpt-4.1")

# Configure the database
db_url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
NIKHIL_DB_NAME = "nikhil_sample.db"

response = requests.get(db_url)

if response.status_code == 200:
    with open(NIKHIL_DB_NAME, "wb") as file:
        file.write(response.content)
    print(f"file downloaded and saved as {NIKHIL_DB_NAME}")
else:
    print(f"Failed to download File. Error : {response.status_code}")

db = SQLDatabase.from_uri(f"sqlite:///{NIKHIL_DB_NAME}")

toolkit = SQLDatabaseToolkit(db=db, llm=nikhil_llm)
nikhil_tools = toolkit.get_tools()

for tool in nikhil_tools:
    print(f"{tool.name}: {tool.description}\n")

get_schema_tool = next(tool for tool in nikhil_tools if tool.name == "sql_db_schema")
run_query_tool = next(tool for tool in nikhil_tools if tool.name == "sql_db_query")
list_tables_tool = next(tool for tool in nikhil_tools if tool.name == "sql_db_list_tables")

get_schema_node = ToolNode([get_schema_tool], name="fetch_schema")
run_query_node = ToolNode([run_query_tool], name="run_sql")

def show_tables(state: MessagesState):
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "nikhil123",
        "type": "tool_call",
    }
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])
    tool_message = list_tables_tool.invoke(tool_call)
    response = AIMessage(f"Available tables: {tool_message.content}")
    return {"messages": [tool_call_message, tool_message, response]}

def fetch_schema(state: MessagesState):
    llm_with_tools = nikhil_llm.bind_tools([get_schema_tool], tool_choice="any")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

make_query_system_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
""".format(
    dialect=db.dialect,
    top_k=5,
)

def make_query(state: MessagesState):
    system_message = {"role": "system", "content": make_query_system_prompt}
    llm_with_tools = nikhil_llm.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_message] + state["messages"])
    return {"messages": [response]}

validate_sql_system_prompt = """
You are a SQL expert with a strong attention to detail.
Double check the {dialect} query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes,
just reproduce the original query.

You will call the appropriate tool to execute the query after running this check.
""".format(dialect=db.dialect)

def validate_sql(state: MessagesState):
    system_message = {
        "role": "system",
        "content": validate_sql_system_prompt,
    }
    tool_call = state["messages"][-1].tool_calls[0]
    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = nikhil_llm.bind_tools([run_query_tool], tool_choice="any")
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id
    return {"messages": [response]}

def should_continue_nikhil(state: MessagesState) -> Literal[END, "validate_sql"]:
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "validate_sql"

builder = StateGraph(MessagesState)
builder.add_node(show_tables)
builder.add_node(fetch_schema)
builder.add_node(get_schema_node, "fetch_schema_node")
builder.add_node(make_query)
builder.add_node(validate_sql)
builder.add_node(run_query_node, "run_sql")

builder.add_edge(START, "show_tables")
builder.add_edge("show_tables", "fetch_schema")
builder.add_edge("fetch_schema", "fetch_schema_node")
builder.add_edge("fetch_schema_node", "make_query")
builder.add_conditional_edges(
    "make_query",
    should_continue_nikhil,
)
builder.add_edge("validate_sql", "run_sql")
builder.add_edge("run_sql", "make_query")

nikhil_agent = builder.compile()
display(Image(nikhil_agent.get_graph().draw_mermaid_png()))

def chat_with_nikhil_agent(message, history):
    response = ""
    for step in nikhil_agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        stream_mode="values",
    ):
        last_message = step["messages"][-1]
        if hasattr(last_message, 'content'):
            response = last_message.content
    return response

def display_nikhil_tables():
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "nikhil123",
        "type": "tool_call",
    }
    tables = list_tables_tool(tool_call)
    return tables

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("#  Nikhil Natural DB - Query your SQL Database with Human Language")

    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown("Ask questions about music tracks, genres, and get insights!")
            chatbot = gr.Chatbot(
                height=500,
                bubble_full_width=False,
            )
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Ask about genres, tracks, or statistics...",
                    show_label=False,
                    scale=4,
                )
                submit = gr.Button("Send", scale=1, variant="primary")
            with gr.Row():
                clear = gr.Button("Clear Chat")
            gr.Examples(
                examples=[
                    "Which genre on average has the longest tracks?",
                    "What are the top 5 most popular genres?",
                    "How many tracks are in each genre?",
                ],
                inputs=msg,
            )
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Available Tables")
            tables_display = gr.Textbox(
                label="Database Tables",
                value=display_nikhil_tables(),
                lines=10,
                interactive=False,
                max_lines=15,
            )
            refresh_btn = gr.Button("🔄 Refresh Tables", size="sm")
            refresh_btn.click(display_nikhil_tables, outputs=tables_display)
    def user(user_message, history):
        return "", history + [[user_message, None]]
    def bot(history):
        user_message = history[-1][0]
        bot_response = chat_with_nikhil_agent(user_message, history)
        history[-1][1] = bot_response
        return history
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    submit.click(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)
demo.launch()
