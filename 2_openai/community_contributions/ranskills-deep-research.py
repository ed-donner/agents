import asyncio
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

import gradio as gr
import requests
from agents import (
    Agent,
    Runner,
    enable_verbose_stdout_logging,
    function_tool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
    set_tracing_export_api_key,
    trace,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from pydantic import BaseModel, Field

os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

load_dotenv(override=True)
logging.basicConfig(level=logging.WARNING)

set_tracing_disabled(False)
logger = logging.getLogger('dr')
logger.setLevel(logging.DEBUG)


LLM_PROVIDERS = {
    # api_key, base_url, model
    'ollama_cloud': (os.getenv('OLLAMA_API_KEY'), 'https://ollama.com/v1', 'gpt-oss:120b'),
    'cerebras': (os.getenv('CEREBRAS_API_KEY'), 'https://api.cerebras.ai/v1', 'gpt-oss-120b'),
}
LLM_PROVIDER = 'cerebras'
api_key, base_url, model = LLM_PROVIDERS[LLM_PROVIDER]
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')

client = AsyncOpenAI(api_key=api_key, base_url=base_url)

set_default_openai_api('chat_completions')
set_default_openai_client(client)
set_tracing_export_api_key(os.getenv('OPENAI_API_KEY'))
enable_verbose_stdout_logging()

screenshots_dir = Path('deep-research-output/screenshots')
screenshots_dir.mkdir(parents=True, exist_ok=True)
reports_dir = Path('deep-research-output/reports')
reports_dir.mkdir(parents=True, exist_ok=True)


def url_to_filename(url: str) -> str:
    return url.replace('https://', '').replace('/', '_').replace(':', '_')


def generate_safe_filename(topic: str, max_length: int = 100) -> str:
    filename = topic.lower()

    filename = re.sub(r'[\s]+', '_', filename)
    filename = re.sub(r'[^a-z0-9_-]', '', filename)

    timestamp = int(time.time())

    if len(filename) > max_length:
        filename = filename[:max_length].strip('_')

    filename = f'{filename}_{timestamp}'

    return filename


def save_report(filename: str, content: str) -> None:
    with open(reports_dir / filename, 'w') as f:
        f.write(content)


@function_tool(name_override='save_report')
def save_report_tool(filename: str, content: str) -> None:
    return save_report(filename, content)


class QueryItem(BaseModel):
    query: str
    reason: str


class QueryItemList(BaseModel):
    original_query: str
    rephrased_query: str | None
    items: list[QueryItem]


async def generate_queries(topic: str, num_queries: int = 5) -> QueryItemList:
    today = datetime.now().strftime('%B %d, %Y')
    system_prompt = f"""
    You are a research planner tasked on {today}.
    Given a topic, generate {num_queries} quality queries that will be used to obtain quality data from external
    sources for review.
    You may rephrase the query if it helps get better results, but remember to maintain the overrall intent.
    Use the rephased query when this happens.
    """.strip()

    agent = Agent(
        name='search_query_generator',
        model=model,
        instructions=system_prompt,
        output_type=QueryItemList,
    )
    result = await Runner.run(agent, input=topic)

    return result.final_output_as(QueryItemList)


async def _search_with_serpapi(query: str):
    data = {
        'q': query,
        'engine': 'google',
        'api_key': SERPAPI_API_KEY,
    }
    resp = requests.get('https://serpapi.com/search', data=data)
    j = resp.json()
    organic_results = j['organic_results']

    results = [{'title': item['title'], 'url': item['link']} for item in organic_results]
    return results


async def _search_with_duckduckgo(query: str):
    from ddgs import DDGS

    search_results = DDGS().text(query=query, region='us-en', max_results=5)
    # Result field: title, href, body (excerpt)
    for r in search_results:
        print(r)

    return search_results


async def perform_online_search(query: str):
    return await _search_with_serpapi(query)


async def aggregate_online_search_results(query_result: QueryItemList) -> list[dict]:
    tasks = [perform_online_search(item.query) for item in query_result.items]
    search_results = await asyncio.gather(*tasks)
    result = [
        {'title': item['title'], 'url': item['url']}
        for sublist in search_results
        for item in sublist
    ]
    return result


class SearchResultItem(BaseModel):
    title: str
    url: str
    score: float = Field(0, description='Overall score for this search result between 0 to 5')


class SearchResultItemList(BaseModel):
    items: list[SearchResultItem]


async def pick_best_preliminary_search_results(
    topic: str, preliminary_search_results, num: int = 10
):
    system_prompt = f"""
    You are a research assistant tasked to select the most relevant search results for a given topic.

    Topic:
    {topic}

    Select the best {num} by following the rules:
    - review each item in relations to the topic
    - score/rate the item
    - present the most relevant results from the provided search results
    """.strip()

    options = '\n\n'.join(
        [
            f'{idx}\nTitle: {item["title"]}\nURL: {item["url"]}'
            for idx, item in enumerate(preliminary_search_results, start=1)
        ]
    )

    agent = Agent(
        name='search_result_selector',
        model=model,
        instructions=system_prompt,
        output_type=SearchResultItemList,
    )

    result = await Runner.run(agent, input=f'Search Results: {options}')
    return result.final_output_as(SearchResultItemList)


async def fetch_page_content(url: str) -> str:
    import random

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    ]
    stealth = Stealth(init_scripts_only=True)
    async with async_playwright() as p:
        try:
            logger.info(f'Fetching: {url}')

            file_name = url_to_filename(url)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(user_agents))
            await stealth.apply_stealth_async(context)

            # await context.add_init_script(code=stealth.main_script)
            page = await context.new_page()
            await page.goto(url, timeout=5 * 60_000)
            await page.evaluate("""() => {
                    const badTags = ['nav', 'footer', 'aside', 'script', 'style'];
                    badTags.forEach(tag => {
                        document.querySelectorAll(tag).forEach(el => el.remove());
                    });
                }""")
            await page.screenshot(
                path=screenshots_dir / f'{file_name}.png', type='png', full_page=True
            )
            timeout = 2 * 60_000
            content = await page.inner_text('body', timeout=timeout)
            await browser.close()

            logger.info(f'Done Fetching: {url}')
            return content
        except Exception as e:
            logger.error(f'Failed {url}: {e}')
            return ''


async def aggregate_page_contents(search_results: SearchResultItemList) -> str:
    tasks = [fetch_page_content(item.url) for item in search_results.items]
    contents = await asyncio.gather(*tasks)

    context = '\n\n'.join(
        [
            f'Source:{search_result.url}:\n {content}'
            for search_result, content in zip(search_results.items, contents)
            if len(content) > 200
        ]
    )

    return context


async def produce_search_report(query: str, context: str):
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

    agent = Agent(
        name='report_writer',
        instructions=system_prompt,
        model=model,
    )
    result = await Runner.run(
        agent,
        input=f'Produce the report for: Topic: {query} \n\nContext: {context}',
    )
    return result.final_output


async def deep_research_pipeline(
    topic: str,
    num_generated_queries: int,
    num_filtered_search_results: int,
    email_address: str,
):
    with trace('Deep Research'):
        yield None, None, '', '⏳ Planning queries...'

        query_list = await generate_queries(topic, num_generated_queries)
        topic = query_list.rephrased_query or topic
        yield (
            query_list.model_dump(),
            None,
            '',
            '🔍 Performing web searches...',
        )

        raw_results = await aggregate_online_search_results(query_list)
        filtered = await pick_best_preliminary_search_results(
            topic, raw_results, num_filtered_search_results
        )
        sources = [item.url for item in filtered.items]
        yield (
            query_list.model_dump(),
            {'selected_sources': sources},
            '',
            '📥 Fetching page content...',
        )

        full_content = await aggregate_page_contents(filtered)
        preview = ''
        yield (
            query_list.model_dump(),
            {'selected_sources': sources},
            preview,
            '✍️ Writing final report...',
        )

        report = await produce_search_report(topic, full_content)
        yield (
            query_list.model_dump(),
            {'selected_sources': sources},
            preview,
            report,
        )
        save_report(generate_safe_filename(topic) + '.md', report)


title = '🔍 Deep Research Tool'
with gr.Blocks(title=title) as demo:
    gr.Markdown(f'## {title}')
    gr.Markdown('### 💡 Tip: Try rephrasing your topic for different results.')

    with gr.Row():
        num_generated_queries = gr.Number(
            label='Number of Search Queries Generated',
            info='Relevant search queries generated',
            value=5,
            interactive=True,
            minimum=1,
            maximum=10,
            step=1,
        )
        num_filtered_search_results = gr.Number(
            label='Number of Filtered Search Results',
            info='Picks the best sources',
            value=5,
            interactive=True,
            minimum=1,
            maximum=20,
            step=1,
        )
        email_tb = gr.Textbox(
            label='Email Address',
            type='email',
            placeholder='Optional email address',
            info='Receive a summary of the report via email.',
        )

    topic = gr.Textbox(
        label='Enter your research topic',
        placeholder='e.g., FinTech Startups In Ghana',
    )
    gr.Examples(
        label='Sample Topics',
        examples=[
            ['AI in QA testing'],
            ['FinTech Startups In Ghana'],
            ['Blockchain in Healthcare'],
            ['AI Replacing The Workforce'],
        ],
        inputs=topic,
    )
    run_btn = gr.Button('Start Research')

    with gr.Row():
        with gr.Column():
            gr.Markdown('### 1. 🔎 Query Plan')
            query_plan_json = gr.JSON()

            gr.Markdown('### 2. 🌐 Selected Sources')
            sources_list = gr.JSON()

            gr.Markdown('### 3. 📄 Fetched Content (Preview)')
            content_preview = gr.Textbox(lines=6, max_lines=10, interactive=False, visible=False)

            gr.Gallery(value=list(screenshots_dir.glob('*.png')), label='🖼️ Images')
        with gr.Column():
            gr.Markdown('### 4. 📝 Final Report')
            report_md = gr.Markdown()


    run_btn.click(
        fn=deep_research_pipeline,
        inputs=[topic, num_generated_queries, num_filtered_search_results, email_tb],
        outputs=[query_plan_json, sources_list, content_preview, report_md],
        queue=True,
    )


demo.launch(share=False, debug=True)
