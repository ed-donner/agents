from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from typing import List, Any, Dict
from sidekick_tools import other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools = await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    Your main task is to provide Google Scholar search results to the user.
    You have a tool named google_scholar to search for papers on Google Scholar — call it with a focused query.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    Success criteria for this turn:
    {state.get("success_criteria", "Answer clearly using Scholar when relevant.")}
    """

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))

        graph_builder.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "end": END},
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        msgs = [HumanMessage(content=message)] if isinstance(message, str) else message
        state = {
            "messages": msgs,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
        }
        result = await self.graph.ainvoke(state, config=config)
        last = result["messages"][-1]
        content = getattr(last, "content", None) or str(last)
        user = {"role": "user", "content": message if isinstance(message, str) else str(message)}
        reply = {"role": "assistant", "content": content}
        return history + [user, reply]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
            except RuntimeError:
                asyncio.run(self.browser.close())