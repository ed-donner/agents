from dotenv import load_dotenv
from langchain.globals import set_verbose, set_debug
from langchain_groq import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain_core.output_parsers import PydanticOutputParser

from prompts import *
from states import *
from tools import write_file, read_file, get_current_directory, list_files

load_dotenv(override=True)
set_debug(True)
set_verbose(True)

llm = ChatGroq(model="openai/gpt-oss-120b")


def _extract_text_from_response(resp) -> str:
    """
    Robust extractor for model text from different response wrapper shapes.
    """
    # Common attribute names:
    if resp is None:
        return ""
    if hasattr(resp, "content"):
        return resp.content
    if hasattr(resp, "text"):
        return resp.text
    try:
        gens = getattr(resp, "generations", None)
        if gens:
            first = gens[0]
            if isinstance(first, list):
                return first[0].text
            else:
                return first.text
    except Exception:
        pass
    return str(resp)


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan using a Pydantic parser."""
    user_prompt = state["user_prompt"]

    parser = PydanticOutputParser(pydantic_object=Plan)
    format_instructions = parser.get_format_instructions()

    messages = [
        {"role": "system", "content": "You are the PLANNER agent. Produce a Plan as strict JSON."},
        {"role": "system", "content": format_instructions},
        {"role": "user", "content": planner_prompt(user_prompt)},
    ]

    raw = llm.invoke(messages, temperature=0)
    text = _extract_text_from_response(raw)

    plan_obj = parser.parse(text)
    if isinstance(plan_obj, dict):
        plan = Plan.model_validate(plan_obj)
    else:
        plan = plan_obj

    return {"plan": plan}


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan using Pydantic parser."""
    plan: Plan = state["plan"]

    parser = PydanticOutputParser(pydantic_object=TaskPlan)
    format_instructions = parser.get_format_instructions()

    messages = [
        {"role": "system", "content": "You are the ARCHITECT agent. Produce a TaskPlan as strict JSON."},
        {"role": "system", "content": format_instructions},
        {"role": "user", "content": architect_prompt(plan=plan.model_dump_json())},
    ]

    raw = llm.invoke(messages, temperature=0)
    text = _extract_text_from_response(raw)

    taskplan_obj = parser.parse(text)
    if isinstance(taskplan_obj, dict):
        taskplan = TaskPlan.model_validate(taskplan_obj)
    else:
        taskplan = taskplan_obj

    taskplan.plan = plan
    return {"task_plan": taskplan}


def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.run(current_task.filepath)

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Use write_file(path, content) to save your changes."
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)

    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]})

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


graph_builder = StateGraph(dict)

graph_builder.add_node("planner", planner_agent)
graph_builder.add_node("architect", architect_agent)
graph_builder.add_node("coder", coder_agent)

graph_builder.add_edge("planner", "architect")
graph_builder.add_edge("architect", "coder")
graph_builder.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph_builder.set_entry_point("planner")
agent = graph_builder.compile()


if __name__ == "__main__":
    result = agent.invoke({"user_prompt": "Build a colourful modern todo app in html css and js"},
                          {"recursion_limit": 10})
    print("Final State:", result)
