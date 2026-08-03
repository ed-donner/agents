import os
import logging
import json
import time
from datetime import datetime
from typing import TypedDict, Literal, Any
from enum import StrEnum

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.types import Command, RetryPolicy, StateSnapshot, interrupt
from tavily import TavilyClient
from weasyprint import HTML

from llm import llm, memory
from common import logger, pretty_print, reports_dir
from common.utils import write_report, generate_safe_filename

from schemas import SearchQueryList, EvaluatedSearchQueryList, EvaluatedSearchQuery

load_dotenv(override=True)

client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))


class Node(StrEnum):
    GENERATE_SEARCH_QUERIES = 'generate_search_queries'
    EVALUATE_SEARCH_QUERIES = 'evaluate_search_queries'
    APPROVE_QUERIES = 'approve_queries'
    SELECT_TOP_K_QUERIES = 'select_top_k_queries'
    PERFORM_SEARCH = 'perform_search'
    FETCH_PAGE_CONTENTS = 'fetch_page_contents'
    PRODUCE_REPORT = 'produce_report'


class ResearcherState(TypedDict):
    topic: str
    num_queries: int = 5  # I will have to look into how to pass this from the parent state
    queries_approved: bool
    query_evaluation_feedback: str
    search_queries: list[str]
    evaluated_search_queries: Any
    selected_queries: list[EvaluatedSearchQuery]
    search_results: list[str]
    page_contents: str


builder = StateGraph(ResearcherState)


def generate_search_queries(state: ResearcherState):
    num_queries = 10
    today = datetime.now().strftime('%B %d, %Y')

    system_prompt = f"""
    You are a research planner tasked on {today}.
    Given a topic, generate {num_queries} quality queries that will be used to obtain quality data from external
    sources for review.
    You may rephrase the query if it helps get better results, but remember to maintain the overrall intent.
    Use the rephased query when this happens.
    """.strip()

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': state['topic']},
    ]

    model_with_output = llm.with_structured_output(SearchQueryList)
    result = model_with_output.invoke(messages)

    print('LLLLL Call Response')
    print(result)
    logger.debug(f'Generating search queries: {state}')
    return {
        'search_queries': result,
    }


def evaluate_search_queries(state: ResearcherState):
    import random

    logger.debug(f'Evaluating search queries: {state}')

    system_prompt = f"""
    You are a research evaluator tasked on.
    Given a list of search queries, evaluate the relevance, actionability, and specificity of the queries.
    Return a list of evaluated search queries.

    

    Evaluation Criteria:
    - Relevance: How relevant is the query to the topic?
    - Actionability: How actionable is the query?
    - Specificity: How specific is the query?

    """.strip()

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'Search Queries: {state["search_queries"].model_dump_json()}'},
    ]
    model_with_output = llm.with_structured_output(EvaluatedSearchQueryList)
    result = model_with_output.invoke(messages)

    logger.debug(f'Evaluated search queries: {result}')
    return {
        'evaluated_search_queries': result,
    }

    # feedback = random.choice(['passed', 'failed'])
    # logger.debug(f'Evaluating search queries results: {feedback}')
    # return {
    #         'query_evaluation_feedback': feedback,
    #     }
    # return Command(
    #     update={
    #         'query_evaluation_feedback': feedback,
    #     },
    #     # goto=feedback,
    # )
    # return random.choice([True, False])


def select_top_k_queries(state: ResearcherState):
    scored_queries = state['evaluated_search_queries'].items
    scored_queries.sort(key=lambda x: x.relevance + x.actionability + x.specificity, reverse=True)

    # logger.debug(f'Scored queries: {scored_queries}')
    pretty_print('Scored Queries', state)
    selected_queries = scored_queries[: state['num_queries']]
    return {
        'selected_queries': selected_queries,
    }


def route(state: ResearcherState):
    return state['query_evaluation_feedback']
    # if state['query_evaluation_feedback'] == 'rejected':
    #     return 'failed'
    # else:
    #     return 'passed'


def route_human_decision(state: ResearcherState):
    return 'approved' if state['queries_approved'] else 'rejected'


def user_approval(state: ResearcherState):
    approved = interrupt(
        {
            # type, stage
            'message': 'Do you want to approve the search queries?',
            'data': state['search_queries'],  # .model_dump_json(),
        }
    )

    logger.debug(f'Approved by user: {approved}')

    return {'queries_approved': approved}
    # if approved:
    #     # return Command(goto='perform_search')
    #     return 'approved'
    # else:
    #     # return Command(goto=END)
    #     return 'rejected'


def perform_search(state: ResearcherState):
    aggregated_results = []
    for query in state['selected_queries']:
        results = client.search(query=query.query, search_depth='basic', max_results=5)
        aggregated_results.extend(results.get('results', [])[:1])
        pretty_print(f'Search results: {query.query}', results, 120)
        time.sleep(1)
        # logger.debug(f'Search results: {results}')

    logger.debug(f'Performing search: {state}')
    return {
        'search_results': aggregated_results,
    }


def fetch_page_contents(state: ResearcherState):
    urls = [result['url'] for result in state['search_results']]
    results = client.extract(urls=urls, timeout=90, format='markdown')
    contents = '\n\n'.join(
        [
            f'Source: {result["url"]}\n{result["raw_content"]}'
            for result in results.get('results', [])
        ]
    )
    pretty_print('Page contents', contents, 120)

    return {
        'page_contents': contents,
    }


def produce_report(state: ResearcherState):
    context = state['page_contents']

    system_prompt = """
    You are a research assistant only limited to the context given.
    Tasked to create a professional, detailed report.
    You are to only produce a report based on the provided context, if there is no context, do not
    generate a report. The report should be comprehensive and well-structured and in a markdown format.

    Rules:
    - From the topic, generate an title for the report
    - Any details you may require for the report creation, derive them from the provided topic
    - Do not ask the any further clarifications, you have all is required to accomplish the task
    - Present relevant information only from the provided content
    - Group findings under appropriate headings or sections
    - Ignore navigation items in your analysis
    - For credibility, cite all sources used in the report
    """.strip()

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'Topic: {state["topic"]} \n\nContext: {context}'},
    ]

    result = llm.invoke(messages)

    markdown_content = result.content

    base_filename = generate_safe_filename(state['topic'])

    markdown_filename = base_filename + '.md'
    write_report(markdown_filename, markdown_content)

    html_filename = base_filename + '.html'
    html_content = create_html_report(markdown_content)
    write_report(html_filename, html_content)

    # pdf_filename = base_filename + '.pdf'
    # HTML(html_content).write_pdf(reports_dir, pdf_filename)

    return {}


def create_html_report(markdown_content: str):
    system_prompt = """
    You are a HTML report generator.
    Tasked to create a professional, detailed HTML report the provided markdown content.
    Just output the HTML content, no other text or explanation.
    """.strip()

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'Content: {markdown_content}'},
    ]

    result = llm.invoke(messages)
    return result.content


# workflow.add_node('greet', greet, retry_policy=RetryPolicy(max_attempts=3))

builder.add_node(Node.GENERATE_SEARCH_QUERIES, generate_search_queries)
builder.add_node(Node.EVALUATE_SEARCH_QUERIES, evaluate_search_queries)
builder.add_node(Node.APPROVE_QUERIES, user_approval)
builder.add_node(Node.SELECT_TOP_K_QUERIES, select_top_k_queries)
builder.add_node(Node.PERFORM_SEARCH, perform_search)
builder.add_node(Node.FETCH_PAGE_CONTENTS, fetch_page_contents)
builder.add_node(Node.PRODUCE_REPORT, produce_report)

builder.add_edge(START, Node.GENERATE_SEARCH_QUERIES)
builder.add_edge(Node.GENERATE_SEARCH_QUERIES, Node.EVALUATE_SEARCH_QUERIES)
builder.add_edge(Node.EVALUATE_SEARCH_QUERIES, Node.SELECT_TOP_K_QUERIES)
builder.add_edge(Node.SELECT_TOP_K_QUERIES, Node.APPROVE_QUERIES)
# builder.add_conditional_edges(
#     Node.EVALUATE_SEARCH_QUERIES,
#     route,
#     {
#         'failed': Node.GENERATE_SEARCH_QUERIES,
#         'passed': Node.USER_APPROVAL, # Come up with a better name for this node
#     },
# )
builder.add_conditional_edges(
    Node.APPROVE_QUERIES,
    route_human_decision,
    {
        'rejected': END,
        'approved': Node.PERFORM_SEARCH,
    },
)

# workflow.add_edge('needs_approval', END)
builder.add_edge(Node.PERFORM_SEARCH, Node.FETCH_PAGE_CONTENTS)
builder.add_edge(Node.FETCH_PAGE_CONTENTS, Node.PRODUCE_REPORT)
builder.add_edge(Node.PRODUCE_REPORT, END)
