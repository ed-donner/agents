import os
import json
import io
from PIL import Image
from datetime import datetime
from typing import Any, TypedDict
import tempfile

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.types import Command, RetryPolicy, StateSnapshot, interrupt
import operator
import gradio as gr
from pydantic import BaseModel

from schemas import IntentClassification
from llm import llm, memory
from common import logger
from agents import coder_builder, researcher_builder
from agents.researcher import ResearcherState

load_dotenv(override=True)

os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'


class State(TypedDict):
    # class State(ResearcherState):
    intent: str
    topic: str
    num_queries: int = 5
    research_result: Any
    code_result: Any


workflow = StateGraph(State)


def classify_intent(state: State):
    system_prompt = f"""
    You are a research planner tasked on {datetime.now().strftime('%B %d, %Y')}.
    Given a topic, classify the intent of the user's request into one of the following categories:
    - research
    - coding
    - unknown

    If the intent is not clear, return 'unknown'.
    """.strip()
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': state['topic']},
    ]
    model_with_output = llm.with_structured_output(IntentClassification)
    result = model_with_output.invoke(messages)

    logger.debug(f'Intent classification: {result}')
    return {'intent': result.intent}
    # return Command(update={'intent': result.intent})
    # return {'intent': result.intent}


def research(state: State):
    # result = researcher_agent.invoke({'topic': state['topic'], 'num_queries': 5})
    result = researcher_agent.invoke({'topic': state['topic'], 'num_queries': 5}, config=config)
    return {'research_result': result}


def code(state: State):
    # result = code_agent.invoke({'topic': state['topic']})
    return {'code_result': 'Unimplemented but coming soon!'}


def route_to_specialist(state: State):
    if state['intent'] == 'research':
        return 'research'
    else:
        return 'code'


researcher_agent = researcher_builder.compile()
coder_agent = coder_builder.compile()

# workflow.add_node('greet', greet, retry_policy=RetryPolicy(max_attempts=3))
workflow.add_node('classify_intent', classify_intent)
# workflow.add_node('research', research)
# workflow.add_node('code', code)

# EXPERIMENTATION: SSwitched to subgraphs as nodes directly.
workflow.add_node('researcher', researcher_agent)
workflow.add_node('coder', coder_agent)

workflow.add_edge(START, 'classify_intent')
workflow.add_conditional_edges(
    'classify_intent',
    route_to_specialist,
    {
        'research': 'researcher',
        'code': 'coder',
    },
)
workflow.add_edge('researcher', END)
workflow.add_edge('coder', END)

# workflow.add_node('greet', greet, retry_policy=RetryPolicy(max_attempts=3))
config = {'configurable': {'thread_id': '101'}}
agent = workflow.compile(checkpointer=memory)

with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
    tmp.write(agent.get_graph(xray=True).draw_mermaid_png())
    # tmp.flush()
    # tmp.close()

print(tmp.name)


# state: State = {'topic': 'AI'}
# agent.invoke(state, config=config)
# logger.debug('Here we are')
# approval = input('Do you want to approve the search queries (Y/N)?')

# agent.invoke(Command(resume=approval.lower()[0] in ['y'] ), config=config)


def run_workflow(topic):
    state: State = {'topic': topic, 'num_queries': 5}

    # try:
    logger.debug('Running workflow')
    result = agent.invoke(state, config=config)
    snapshot = agent.get_state(config, subgraphs=True)

    print('\n' + '*' * 80)
    print('Snapshot')
    print(snapshot)
    print('*' * 80 + '\n')

    # Subgraphs structure is different from the regular nodes.
    # Investigate this more.
    if snapshot.next:
        # yield gr.update(visible=True)
        return handle_interrupt(snapshot)

    logger.debug('\n' + '*' * 80)
    logger.debug('Research State')
    logger.debug(snapshot.subgraphs['research'].get_state(config))

    # yield from handle_interrupt(snapshot)
    # except Exception as e:
    #     logger.error(f'Error running workflow: {str(e)}')
    #     return gr.skip(), gr.skip()

    return gr.skip(), gr.skip()
    # logger.debug('Here we are')
    # approval = input('Do you want to approve the search queries (Y/N)?')

    # agent.invoke(Command(resume=approval.lower()[0] in ['y'] ), config=config)


def handle_interrupt(snapshot: StateSnapshot):
    import json

    for task in snapshot.tasks:
        interrupt = task.interrupts[0]
        print('\n\n\n')
        print(interrupt)
        print(type(interrupt))
        print(interrupt.value.get('message'))
        data = interrupt.value.get('data')

        logger.debug(f'Data type: {type(data)}')
        if isinstance(data, BaseModel):
            details = data.model_dump_json(indent=4)
        else:
            details = data
        message = f'#### {interrupt.value.get("message")}\n```json\n{details}\n```'
        # yield interrupt.get('message'), gr.update(visible=True), gr.update(value=interrupt.get('data'))
        # yield  gr.update(visible=True), gr.update(value=message)
        # return
        return gr.update(visible=True), gr.update(value=message)
        # yield  gr.update(visible=True), 'Lovely message'
        # yield  gr.update(visible=True), interrupt.get('message')
        # logger.debug(f'Task: {task.interrupts[0]}')
    # yield gr.update(visible=True)
    return gr.skip(), gr.skip()


# def handle_approval(thread_id: str, approved: bool):
def handle_approval(approved: bool):
    logger.debug(f'Handling approval: {approved}')
    config = {'configurable': {'thread_id': '101'}}
    try:
        result = agent.invoke(Command(resume=approved), config=config)

        logger.debug(f'Results after resumption: {result}')
    except Exception as e:
        logger.error(f'Error handling approval: {str(e)}')

    return gr.update(visible=False)


title = '🧰 Skills Toolbox'

with gr.Blocks(title=title, theme=gr.themes.Monochrome()) as demo:
    gr.Markdown(f'## {title}')

    gr.Image(tmp.name, label='Workflow Diagram')

    session = gr.State({'auto_approve': False})

    topic_tb = gr.Textbox('How to become an AI Engineer', label='Topic')

    gr.Examples(
        label='Sample Topics',
        examples=[
            ['Write a Go backend program that calculates simple and compound interests'],
            ['FinTech Startups In Ghana'],
            ['Blockchain in Healthcare'],
            ['AI Replacing The Workforce'],
        ],
        inputs=topic_tb,
    )
    start_btn = gr.Button('Start')

    with gr.Column(visible=False) as approval_group:
        approval_info = gr.Markdown(value='#### 🕒 Waiting for approval...')
        with gr.Row() as decision:
            approve_btn = gr.Button('✅ Approve')
            reject_btn = gr.Button('❌ Reject')
        approval_message = gr.Markdown()

    start_btn.click(fn=run_workflow, inputs=[topic_tb], outputs=[approval_group, approval_message])
    approve_btn.click(lambda: handle_approval(True), outputs=[approval_group])
    reject_btn.click(lambda: handle_approval(False), outputs=[approval_group])

demo.launch(debug=True)
