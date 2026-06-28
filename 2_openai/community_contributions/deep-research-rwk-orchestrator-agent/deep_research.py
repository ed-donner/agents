""" point of entry for the deep research project 
    query_agent to receive and (if necessary) refine the query
    orchestrator_agent to conduct research and to produces the final report
    pulish_agent prints the report to a file

    calls run which calls ResearchManager().run(query) -- the research_manager, which:
        calls plan_searches which calls planner_agent to produce WebSearchPlan
        calls perform_searches which calls search_agent to produce SearchResults
        calls filter_results which calls filter_agent to produce FilteredResults
        calls write_report which calls writer_agent to produce ReportData
        call review_report which calls review_agent to produce ReviewResult
            if review_agent finds the report not acceptable, call write_report again
        calls publish_email which calls publish_report to produce an html report file

 """

import gradio as gr
import asyncio
from dotenv import load_dotenv
from agents import Runner

from report_manager import Report_Manager
from query_agent import query_agent, Query


load_dotenv(override=True)


def build_transcript(message, history) -> str:
    '''
    Build a cumulative transcript of the query-refinement conversation:
    the user's messages and the agent's clarifying questions.
    '''
    lines = []
    for turn in history:
        content = turn["content"]
        if turn["role"] == "user":
            lines.append(f"user: {content}")
        elif isinstance(content, str) and content.startswith("Question:"):
            lines.append(f"you (the editor): {content}")
    lines.append(f"user: {message}")
    return "\n".join(lines)


async def chat_response(message, history):
    '''
    Evaluate the user's message aka query; 
    yield a question to clarify the query if necessary,
    or run the research and yield the report if the query is clear
    Args:
        message: the message from the user
        history: the history of the chat as a list of dicts
            [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}, ...]
    Yields:
        progress updates, a clarifying question, or the final report
    '''

    # progress lines in a list and re-yield the joined log to show a growing log.
    progress = ["**Query agent started** *(evaluating the query ...)*"]
    yield progress[0]

    # 2. Evaluate the conversation so far, so the agent remembers its own
    #    questions and the user's answers (not just the latest message)
    query_result = await Runner.run(
        query_agent,
        f"Conversation so far:\n{build_transcript(message, history)}"
    )
    evaluation = query_result.final_output  # a Query object
    print(evaluation)
    progress.append("**Query agent completed.**")
    yield "\n\n".join(progress)

    # 3. If the query is unclear, send the clarifying question back to the user
    #    (a plain "Question: ..." message, so build_transcript can find it later)
    if not evaluation.is_clear:
        yield f"Question: {evaluation.question}"
        return

    # 4. The query is clear: run the research, streaming each progress line
    #    (agent and tool open/close events) into the growing log
    manager = Report_Manager()
    async for status in manager.run(evaluation.query):
        progress.append(status)
        yield "\n\n".join(progress)

    # 5. Show the final report below the completed progress log
    yield "\n\n".join(progress) + "\n\n---\n\n" + manager.report.markdown_report


deep_research_chatbot = gr.ChatInterface(
    fn=chat_response, 
    title="Deep Research",
    description="Type a message to start an interactive conversation!"
)

if __name__ == "__main__":
    deep_research_chatbot.launch(
        theme=gr.themes.Default(primary_hue="sky"),
        inbrowser=True    
    )