import os
import uuid
import sqlite3
import json
import pathlib
import gradio as gr
import hashlib
from typing import TypedDict, Literal
from dotenv import load_dotenv

from datetime import datetime
from trustcall import create_extractor
from typing import Optional
from pydantic import BaseModel, Field

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import merge_message_runs, HumanMessage, SystemMessage

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

from langchain_openai import ChatOpenAI


load_dotenv(override=True)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0, top_p=0.9, max_tokens=4096)


# Helps inspect the tool calls made by Trustcall
class Spy:
    def __init__(self):
        self.called_tools = []

    def __call__(self, run):
        # Helps collect information about the tool calls made by the extractor.
        q = [run]
        while q:
            r = q.pop()
            if r.child_runs:
                q.extend(r.child_runs)
            if r.run_type == "chat_model":
                self.called_tools.append(
                    r.outputs["generations"][0][0]["message"]["kwargs"]["tool_calls"]
                )


# Helper function to extract tool info
def extract_tool_info(tool_calls, schema_name="Memory"):
    """Extract information from tool calls for both patches and new memories.
    
    Args:
        tool_calls: List of tool calls from the model
        schema_name: Name of the schema tool (e.g., "Memory", "ToDo", "Profile")
    """
    changes = []
    
    for call_group in tool_calls:
        for call in call_group:
            if call['name'] == 'PatchDoc':
                patches = call['args'].get('patches', [])
                for patch in patches:
                    op = patch.get('op', 'replace')
                    changes.append({
                        'type': 'update',
                        'op': op,
                        'doc_id': call['args']['json_doc_id'],
                        'planned_edits': call['args'].get('planned_edits', ''),
                        'path': patch.get('path', ''),
                        'value': patch.get('value'),
                    })
            elif call['name'] == schema_name:
                changes.append({
                    'type': 'new',
                    'value': call['args']
                })

    result_parts = []
    for change in changes:
        if change['type'] == 'update':
            op = change['op']
            doc_id = change['doc_id']
            plan = change['planned_edits']
            if op == 'remove':
                result_parts.append(
                    f"Document {doc_id} — removed {change['path']}\n"
                    f"Plan: {plan}"
                )
            else:
                result_parts.append(
                    f"Document {doc_id} — {op} {change['path']}\n"
                    f"Plan: {plan}\n"
                    f"Value: {change['value']}"
                )
        else:
            result_parts.append(
                f"New {schema_name} created:\n"
                f"Content: {change['value']}"
            )
    
    return "\n\n".join(result_parts)


# Update memory tool
class UpdateMemory(TypedDict):
    """Decision on what memory type to update"""
    update_type: Literal['user', 'todo', 'instructions']


class Profile(BaseModel):
    """This is the profile of the user you are chatting with"""
    name: Optional[str] = Field(description="The user's name", default=None)
    location: Optional[str] = Field(description="The user's location", default=None)
    job: Optional[str] = Field(description="The user's job", default=None)
    connections: list[str] = Field(
        description="Personal connection of the user, such as family members, friends, or coworkers",
        default_factory=list
    )
    interests: list[str] = Field(
        description="Interests that the user has", 
        default_factory=list
    )


class ToDo(BaseModel):
    """This is the ToDo list of the user you are chatting with"""
    task: str = Field(description="The task to be completed.")
    time_to_complete: Optional[int] = Field(description="Estimated time to complete the task (minutes).")
    deadline: Optional[datetime] = Field(
        description="When the task needs to be completed by (if applicable)",
        default=None
    )
    solutions: list[str] = Field(
        description="List of specific, actionable solutions (e.g., specific ideas, service providers, or concrete options relevant to completing the task)",
        min_items=1,
        default_factory=list
    )
    status: Literal["not started", "in progress", "done", "archived"] = Field(
        description="Current status of the task",
        default="not started"
    )

# Trustcall extractor for updating the user profile 
# It helps in updating/inserting new memory to existing memory
profile_extractor = create_extractor(
    model,
    tools=[Profile],
    tool_choice="Profile",
)


# PROMPTS
MODEL_SYSTEM_MESSAGE = """You are a helpful chatbot. 
You are designed to be a companion to a user, helping them keep track of their ToDo list.

You have a long term memory which keeps track of three things:
1. The user's profile (general information about them) 
2. The user's ToDo list
3. General instructions for updating the ToDo list

Here is the current User Profile (may be empty if no information has been collected yet):
<user_profile>
{user_profile}
</user_profile>

Here is the current ToDo List (may be empty if no tasks have been added yet):
<todo>
{todo}
</todo>

Here are the current user-specified preferences for updating the ToDo list (may be empty if no preferences have been specified yet):
<instructions>
{instructions}
</instructions>

Here are your instructions for reasoning about the user's messages:
1. Reason carefully about the user's messages as presented below. 
2. Decide whether any of the your long-term memory should be updated:
- If personal information was provided about the user, update the user's profile by calling UpdateMemory tool with type `user`
- If tasks are mentioned, update the ToDo list by calling UpdateMemory tool with type `todo`
- If the user has specified preferences for how to update the ToDo list, update the instructions by calling UpdateMemory tool with type `instructions`
3. Tell the user that you have updated your memory, if appropriate:
- Do not tell the user you have updated the user's profile
- Tell the user them when you update the todo list
- Do not tell the user that you have updated instructions
4. Err on the side of updating the todo list. No need to ask for explicit permission.
5. Respond naturally to user after a tool call was made to save memories, or if no tool call was made."""


TRUSTCALL_INSTRUCTION = """Reflect on following interaction. 
Use the provided tools to retain any necessary memories about the user. 
Use parallel tool calling to handle updates and insertions simultaneously.
System Time: {time}"""


CREATE_INSTRUCTIONS = """Reflect on the following interaction.
Based on this interaction, update your instructions for how to update ToDo list items. 
Use any feedback from the user to update how they like to have items added, etc.
Your current instructions are:

<current_instructions>
{current_instructions}
</current_instructions>"""


def todo_worker(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Load memories from the store and use them to personalize the chatbot's response."""
    
    user_id = config["configurable"]["user_id"]

    # Retrieve profile memory from the store
    namespace = ("profile", user_id)
    memories = store.search(namespace)
    if memories:
        user_profile = memories[0].value
    else:
        user_profile = None

    # Retrieve task memory from the store
    namespace = ("todo", user_id)
    memories = store.search(namespace)
    todo = "\n".join(f"{mem.value}" for mem in memories)

    # Retrieve custom instructions from strore
    namespace = ("instructions", user_id)
    memories = store.search(namespace)
    if memories:
        instructions = memories[0].value
    else:
        instructions = ""
    
    system_msg = MODEL_SYSTEM_MESSAGE.format(user_profile=user_profile, todo=todo, instructions=instructions)

    # Respond using memory as well as the chat history
    response = model.bind_tools([UpdateMemory], parallel_tool_calls=False).invoke([SystemMessage(content=system_msg)]+state["messages"])

    return {"messages": [response]}

def update_profile(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Reflect on the chat history and update the memory collection."""
    tool_calls = state['messages'][-1].tool_calls
    tool_call_id = tool_calls[0]['id']
    try:
        user_id = config["configurable"]["user_id"]

        namespace = ("profile", user_id)
        existing_items = store.search(namespace)

        tool_name = "Profile"
        existing_memories = ([(existing_item.key, tool_name, existing_item.value)
                              for existing_item in existing_items]
                              if existing_items
                              else None
                            )

        TRUSTCALL_INSTRUCTION_FORMATTED = TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat())
        updated_messages=list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION_FORMATTED)] + state["messages"][:-1]))

        result = profile_extractor.invoke({"messages": updated_messages, 
                                             "existing": existing_memories})

        for r, rmeta in zip(result["responses"], result["response_metadata"]):
            store.put(namespace,
                      rmeta.get("json_doc_id", str(uuid.uuid4())),
                      r.model_dump(mode="json"),
                )
        return {"messages": [{"role": "tool", "content": "updated profile", "tool_call_id": tool_call_id}]}
    except Exception as e:
        return {"messages": [{"role": "tool", "content": f"Error updating profile: {e}", "tool_call_id": tool_call_id}]}

def update_todos(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Reflect on the chat history and update the memory collection."""
    tool_calls = state['messages'][-1].tool_calls
    tool_call_id = tool_calls[0]['id']
    try:
        user_id = config["configurable"]["user_id"]

        namespace = ("todo", user_id)
        existing_items = store.search(namespace)

        tool_name = "ToDo"
        existing_memories = ([(existing_item.key, tool_name, existing_item.value)
                              for existing_item in existing_items]
                              if existing_items
                              else None
                            )

        TRUSTCALL_INSTRUCTION_FORMATTED=TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat())
        updated_messages=list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION_FORMATTED)] + state["messages"][:-1]))

        spy = Spy()
        
        todo_extractor = create_extractor(
            model,
            tools=[ToDo],
            tool_choice=tool_name,
            enable_inserts=True
        ).with_listeners(on_end=spy)

        result = todo_extractor.invoke({"messages": updated_messages, 
                                        "existing": existing_memories})

        for r, rmeta in zip(result["responses"], result["response_metadata"]):
            store.put(namespace,
                      rmeta.get("json_doc_id", str(uuid.uuid4())),
                      r.model_dump(mode="json"),
                )

        todo_update_msg = extract_tool_info(spy.called_tools, tool_name)
        return {"messages": [{"role": "tool", "content": todo_update_msg, "tool_call_id": tool_call_id}]}
    except Exception as e:
        return {"messages": [{"role": "tool", "content": f"Error updating todos: {e}", "tool_call_id": tool_call_id}]}

def update_instructions(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Reflect on the chat history and update the memory collection."""
    tool_calls = state['messages'][-1].tool_calls
    tool_call_id = tool_calls[0]['id']
    try:
        user_id = config["configurable"]["user_id"]
        
        namespace = ("instructions", user_id)
        existing_memory = store.get(namespace, "user_instructions")
            
        system_msg = CREATE_INSTRUCTIONS.format(current_instructions=existing_memory.value if existing_memory else None)
        new_memory = model.invoke([SystemMessage(content=system_msg)]+state['messages'][:-1] + [HumanMessage(content="Please update the instructions based on the conversation")])

        key = "user_instructions"
        store.put(namespace, key, {"memory": new_memory.content})
        return {"messages": [{"role": "tool", "content": "updated instructions", "tool_call_id": tool_call_id}]}
    except Exception as e:
        return {"messages": [{"role": "tool", "content": f"Error updating instructions: {e}", "tool_call_id": tool_call_id}]}

# Conditional edge
def route_message(state: MessagesState, config: RunnableConfig, store: BaseStore) -> Literal[END, "update_todos", "update_instructions", "update_profile"]:
    """Reflect on the memories and chat history to decide whether to update the memory collection."""

    message = state['messages'][-1]
    if len(message.tool_calls) == 0:
        return END
    else:
        tool_call = message.tool_calls[0]
        if tool_call['args']['update_type'] == "user":
            return "update_profile"
        elif tool_call['args']['update_type'] == "todo":
            return "update_todos"
        elif tool_call['args']['update_type'] == "instructions":
            return "update_instructions"
        else:
            raise ValueError

# Create the graph + all nodes and edges
builder = StateGraph(MessagesState)

builder.add_node(todo_worker)
builder.add_node(update_todos)
builder.add_node(update_profile)
builder.add_node(update_instructions)
builder.add_edge(START, "todo_worker")
builder.add_conditional_edges("todo_worker", route_message)
builder.add_edge("update_todos", "todo_worker")
builder.add_edge("update_profile", "todo_worker")
builder.add_edge("update_instructions", "todo_worker")

# Persistent long-term memory (across-thread)
# Uses InMemoryStore backed by a JSON file so memories survive kernel restarts
STORE_FILE = pathlib.Path("memory_store.json")
across_thread_memory = InMemoryStore()

if STORE_FILE.exists():
    for _ns_key, _items in json.loads(STORE_FILE.read_text(encoding="utf-8")).items():
        _ns = tuple(_ns_key.split("::"))
        for _key, _value in _items.items():
            across_thread_memory.put(_ns, _key, _value)

def save_memory_store():
    """Persist all memories to memory_store.json."""
    _creds_path = pathlib.Path("users.json")
    user_ids = list(json.loads(_creds_path.read_text()).keys()) if _creds_path.exists() else []
    data = {}
    for uid in user_ids:
        for ns_type in ["profile", "todo", "instructions"]:
            ns = (ns_type, uid)
            items = across_thread_memory.search(ns)
            if items:
                data[f"{ns_type}::{uid}"] = {item.key: item.value for item in items}
    STORE_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

# Persistent short-term memory (within-thread)
# SQLite checkpointer so conversation history survives kernel restarts
conn = sqlite3.connect("memory_agent.db", check_same_thread=False)
within_thread_memory = SqliteSaver(conn)
within_thread_memory.setup()

# We compile the graph with the checkpointer and store
graph = builder.compile(checkpointer=within_thread_memory, store=across_thread_memory)



# Credentials
CREDS_PATH = pathlib.Path("users.json")

def load_creds() -> dict:
    if CREDS_PATH.exists():
        return json.loads(CREDS_PATH.read_text())
    return {}

def save_creds(creds: dict):
    CREDS_PATH.write_text(json.dumps(creds, indent=2))

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# Per-user thread tracking
THREADS_PATH = pathlib.Path("threads.json")

def load_threads() -> dict:
    if THREADS_PATH.exists():
        return json.loads(THREADS_PATH.read_text())
    return {}

def save_threads(data: dict):
    THREADS_PATH.write_text(json.dumps(data, indent=2))

def get_user_threads(user_id: str) -> list:
    return load_threads().get(user_id, [])

def add_thread(user_id: str, thread_id: str):
    data = load_threads()
    if user_id not in data:
        data[user_id] = []
    if thread_id not in data[user_id]:
        data[user_id].append(thread_id)
        save_threads(data)

def new_thread_id(user_id: str) -> str:
    existing = get_user_threads(user_id)
    n = len(existing) + 1
    tid = f"{user_id}_thread_{n}"
    add_thread(user_id, tid)
    return tid

def load_thread_history(thread_id: str) -> list:
    """Reload chat messages from the SQLite checkpointer for a given thread."""
    try:
        state = graph.get_state({"configurable": {"thread_id": thread_id}})
        if not state or not state.values:
            return []
        history = []
        for msg in state.values.get("messages", []):
            if msg.type == "human":
                history.append({"role": "user", "content": msg.content})
            elif msg.type == "ai" and msg.content and not getattr(msg, "tool_calls", None):
                history.append({"role": "assistant", "content": msg.content})
        return history
    except Exception:
        return []


# Memory helpers
def get_profile(user_id: str) -> str:
    memories = across_thread_memory.search(("profile", user_id))
    if not memories:
        return "No profile saved yet."
    p = memories[0].value
    lines = []
    for key, val in p.items():
        if val:
            label = key.replace("_", " ").title()
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val) if val else "—"
            lines.append(f"**{label}:** {val}")
    return "\n\n".join(lines) if lines else "No profile saved yet."

def get_todos(user_id: str) -> str:
    memories = across_thread_memory.search(("todo", user_id))
    if not memories:
        return "No tasks yet."
    parts = []
    for i, mem in enumerate(memories, 1):
        v = mem.value
        status_icon = {"not started": "⬜", "in progress": "🔶", "done": "✅", "archived": "📦"}.get(v.get("status", ""), "⬜")
        line = f"### {status_icon} {i}. {v.get('task', 'Untitled')}\n"
        if v.get("deadline"):
            line += f"- **Deadline:** {v['deadline']}\n"
        if v.get("time_to_complete"):
            line += f"- **Est. time:** {v['time_to_complete']} min\n"
        line += f"- **Status:** {v.get('status', 'unknown')}\n"
        if v.get("solutions"):
            line += "- **Solutions:** " + "; ".join(str(s) for s in v["solutions"]) + "\n"
        parts.append(line)
    return "\n".join(parts)

def get_instructions(user_id: str) -> str:
    memories = across_thread_memory.search(("instructions", user_id))
    if not memories:
        return "No custom instructions set."
    val = memories[0].value
    if isinstance(val, dict):
        return val.get("memory", str(val))
    return str(val)

def refresh_panels(user_id: str):
    return get_profile(user_id), get_todos(user_id), get_instructions(user_id)


# Auth
def do_register(username, password, confirm):
    if not username.strip():
        return gr.update(), gr.update(), "Username cannot be empty."
    if len(password) < 4:
        return gr.update(), gr.update(), "Password must be at least 4 characters."
    if password != confirm:
        return gr.update(), gr.update(), "Passwords do not match."
    creds = load_creds()
    if username in creds:
        return gr.update(), gr.update(), f"Username **{username}** is already taken."
    creds[username] = hash_pw(password)
    save_creds(creds)
    return gr.update(value=username), gr.update(value=password), f"Account **{username}** created! Switch to the **Login** tab to sign in."

def do_login(username, password):
    if not username.strip() or not password:
        return {}, "Please enter both username and password."
    creds = load_creds()
    if username not in creds or creds[username] != hash_pw(password):
        return {}, "Invalid username or password."
    threads = get_user_threads(username)
    tid = threads[-1] if threads else new_thread_id(username)
    session = {"user": username, "thread_id": tid}
    return session, ""

def on_login_success(session):
    """Show main app, hide auth screen, load the user's latest thread."""
    user = session.get("user", "")
    tid = session.get("thread_id", "")
    threads = get_user_threads(user)
    chat_history = load_thread_history(tid)
    prof, todos, instr = refresh_panels(user)
    return (
        gr.update(visible=False),                          # auth_block
        gr.update(visible=True),                           # app_block
        f"Signed in as **{user}**",                        # welcome_md
        user,                                              # user_id_state
        gr.update(choices=threads, value=tid),             # thread_dropdown
        chat_history,                                      # chatbot
        prof, todos, instr,                                # panels
    )

def do_logout():
    return (
        gr.update(visible=True),                           # auth_block
        gr.update(visible=False),                          # app_block
        "",                                                # welcome_md
        "",                                                # user_id_state
        gr.update(choices=[], value=None),                 # thread_dropdown
        [],                                                # chatbot
        "", "", "",                                        # panels
    )


# Guardrails (TODO: uncomment to implement when ready)
# MAX_INPUT_LENGTH = 500
#
# def input_guardrail(message: str) -> str | None:
#     """Returns an error string if input is rejected, None if OK."""
#     if len(message) > MAX_INPUT_LENGTH:
#         return f"Message too long ({len(message)} chars). Max is {MAX_INPUT_LENGTH}."
#     # Add more checks here: profanity filter, prompt injection detection, etc.
#     return None
#
# def output_guardrail(response: str) -> str:
#     """Sanitize or filter the model's response before showing to user."""
#     # Add checks here: PII redaction, harmful content filter, etc.
#     return response


# Chat handler (streaming enabled)
def respond(message, chat_history, user_id, thread_id):
    if not message.strip() or not user_id:
        yield chat_history, "", *refresh_panels(user_id or "")
        return

    # TODO: uncomment when guardrails are ready
    # rejection = input_guardrail(message)
    # if rejection:
    #     chat_history = chat_history + [
    #         {"role": "user", "content": message},
    #         {"role": "assistant", "content": rejection},
    #     ]
    #     yield chat_history, "", *refresh_panels(user_id)
    #     return

    add_thread(user_id, thread_id)

    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    input_messages = [HumanMessage(content=message)]

    chat_history = chat_history + [{"role": "user", "content": message}]

    assistant_reply = ""
    for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
        last = chunk["messages"][-1]
        if hasattr(last, "content") and last.content and last.type == "ai" and not getattr(last, "tool_calls", None):
            assistant_reply = last.content
            yield chat_history + [{"role": "assistant", "content": assistant_reply}], "", *refresh_panels(user_id)

    save_memory_store()

    # TODO: uncomment when guardrails are ready
    # assistant_reply = output_guardrail(assistant_reply)

    chat_history = chat_history + [
        {"role": "assistant", "content": assistant_reply or "(memory updated)"},
    ]
    yield chat_history, "", *refresh_panels(user_id)

def new_thread(user_id):
    tid = new_thread_id(user_id)
    threads = get_user_threads(user_id)
    return [], gr.update(choices=threads, value=tid), *refresh_panels(user_id)

def switch_thread(thread_id, user_id):
    if not thread_id:
        return [], *refresh_panels(user_id or "")
    chat_history = load_thread_history(thread_id)
    return chat_history, *refresh_panels(user_id)


# UI
with gr.Blocks(
    title="Natural Language ToDo app",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky"),
    css="""
    .panel-box  {border:1px solid #e0e0e0; border-radius:10px; padding:16px; background:#fafbfc;}
    .auth-card  {max-width:420px; margin:80px auto; padding:32px; border:1px solid #dde; border-radius:14px; background:#fff; box-shadow:0 4px 24px rgba(0,0,0,.06);}
    .auth-title {text-align:center; margin-bottom:4px;}
    """
) as demo:

    session_state  = gr.State({})
    user_id_state  = gr.State("")

    # Auth screen
    with gr.Column(visible=True, elem_classes="auth-card") as auth_block:
        gr.Markdown("# 🧠 ToDo Worker", elem_classes="auth-title")
        gr.Markdown("Sign in or create an account to start managing your tasks.", elem_classes="auth-title")

        with gr.Tab("Login"):
            login_user = gr.Textbox(label="Username", placeholder="your username")
            login_pass = gr.Textbox(label="Password", type="password", placeholder="your password")
            login_btn = gr.Button("Sign In", variant="primary")
            login_msg = gr.Markdown("")

        with gr.Tab("Register"):
            reg_user = gr.Textbox(label="Username", placeholder="choose a username")
            reg_pass = gr.Textbox(label="Password", type="password", placeholder="min 4 characters")
            reg_confirm = gr.Textbox(label="Confirm Password", type="password", placeholder="repeat password")
            reg_btn = gr.Button("Create Account", variant="primary")
            reg_msg = gr.Markdown("")

    # Main app (hidden until login)
    with gr.Column(visible=False) as app_block:
        with gr.Row():
            welcome_md = gr.Markdown("")
            gr.Column(scale=3)
            thread_dropdown = gr.Dropdown(label="Thread", choices=[], interactive=True, scale=2)
            new_thread_btn = gr.Button("New Thread", variant="secondary", scale=1)
            logout_btn = gr.Button("Logout", variant="stop", scale=1)

        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Chat", height=500, type="messages",
                    show_copy_button=True,
                    avatar_images=(None, "https://em-content.zobj.net/source/twitter/376/brain_1f9e0.png"),
                )
                with gr.Row():
                    msg_box  = gr.Textbox(placeholder="Type a message…", show_label=False, scale=5)
                    send_btn = gr.Button("Send", variant="primary", scale=1)

            with gr.Column(scale=2):
                with gr.Tab("ToDo List"):
                    todo_panel = gr.Markdown("", elem_classes="panel-box")
                with gr.Tab("Profile"):
                    profile_panel = gr.Markdown("", elem_classes="panel-box")
                with gr.Tab("Instructions"):
                    instructions_panel = gr.Markdown("", elem_classes="panel-box")
                refresh_btn = gr.Button("Refresh Panels", variant="secondary", size="sm")

    # Wiring
    login_success_outputs = [
        auth_block, app_block, welcome_md, user_id_state,
        thread_dropdown, chatbot, profile_panel, todo_panel, instructions_panel,
    ]
    logout_outputs = login_success_outputs

    reg_btn.click(do_register, [reg_user, reg_pass, reg_confirm], [login_user, login_pass, reg_msg])

    login_btn.click(
        do_login, [login_user, login_pass], [session_state, login_msg]
    ).then(
        on_login_success, [session_state], login_success_outputs
    )
    login_pass.submit(
        do_login, [login_user, login_pass], [session_state, login_msg]
    ).then(
        on_login_success, [session_state], login_success_outputs
    )

    logout_btn.click(do_logout, [], logout_outputs)

    send_inputs  = [msg_box, chatbot, user_id_state, thread_dropdown]
    send_outputs = [chatbot, msg_box, profile_panel, todo_panel, instructions_panel]

    send_btn.click(respond, send_inputs, send_outputs)
    msg_box.submit(respond, send_inputs, send_outputs)

    new_thread_btn.click(
        new_thread, [user_id_state],
        [chatbot, thread_dropdown, profile_panel, todo_panel, instructions_panel],
    )
    thread_dropdown.change(
        switch_thread, [thread_dropdown, user_id_state],
        [chatbot, profile_panel, todo_panel, instructions_panel],
    )
    refresh_btn.click(refresh_panels, [user_id_state], [profile_panel, todo_panel, instructions_panel])


if __name__ == "__main__":
    demo.launch(inbrowser=True)
