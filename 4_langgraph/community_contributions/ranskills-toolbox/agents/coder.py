import json
from typing import TypedDict
from enum import StrEnum

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from llm import llm
from common import logger

load_dotenv(override=True)


class TaskPlan(BaseModel):
    plan: list[str] = Field(description='The plan for the task')


class Node(StrEnum):
    PLAN_TASK = 'plan_task'
    IMPLEMENT_TASK = 'implement_task'


class CoderState(TypedDict):
    task: str


builder = StateGraph(CoderState)


def plan_task(state: CoderState):
    print('*' * 80)
    print(json.dumps(state, indent=4))
    system_prompt = f"""
    You are a software engineer tasked with planning and implementing a task.
    Given a task, plan the task into a series of steps.
    """.strip()
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': state['task']},
    ]
    model_with_output = llm.with_structured_output(TaskPlan)
    result = model_with_output.invoke(messages)

    logger.debug(f'Planning task: {state}')
    return {
        'plan': result.plan,
    }


def implement_task(state: CoderState):
    logger.debug(f'Implementing task: {state}')
    return {
        'implementation': 'Implementation of the task',
    }


builder.add_node(Node.PLAN_TASK, plan_task)
builder.add_node(Node.IMPLEMENT_TASK, implement_task)

builder.add_edge(START, Node.PLAN_TASK)
builder.add_edge(Node.PLAN_TASK, Node.IMPLEMENT_TASK)
builder.add_edge(Node.IMPLEMENT_TASK, END)
