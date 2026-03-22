
from __future__ import annotations

import asyncio
import inspect
import uuid
from typing import Any

import gradio as gr
from dotenv import load_dotenv

load_dotenv(override=True)

import compat  
from agents import Runner
from agents.items import HandoffCallItem, ItemHelpers, MessageOutputItem, ToolCallItem, ToolCallOutputItem
from agents.stream_events import RunItemStreamEvent
from orchestrate import (
    ResearchUiContext,
    clarifier_topic_and_prior_from_gradio,
    research_host_agent,
    set_research_progress_queue,
)

try:
    from agents.memory import SQLiteSession
except ImportError:
    SQLiteSession = None  

_USE_SDK_SQLITE_SESSION = SQLiteSession is not None and (
    "session" in inspect.signature(Runner.run_streamed).parameters
)


def _final_output_to_text(final_output) -> str:
    if final_output is None:
        return "_No response from agent._"
    if isinstance(final_output, str):
        return final_output
    return str(final_output)


def _callable_name(item) -> str | None:
    if isinstance(item, ToolCallItem):
        ri = item.raw_item
        n = getattr(ri, "name", None)
        return str(n) if n else None
    if isinstance(item, HandoffCallItem):
        ri = item.raw_item
        n = getattr(ri, "name", None)
        return str(n) if n else None
    return None


async def _merge_stream_events_progress(streamed, progress_q: asyncio.Queue):
    """Interleave SDK stream events with research pipeline progress lines."""
    aiter = streamed.stream_events().__aiter__()
    get_ev = asyncio.create_task(aiter.__anext__())
    get_chunk = asyncio.create_task(progress_q.get())
    stream_done = False

    while not stream_done:
        done, _ = await asyncio.wait({get_ev, get_chunk}, return_when=asyncio.FIRST_COMPLETED)
        if get_chunk in done:
            chunk = get_chunk.result()
            yield "chunk", chunk
            get_chunk = asyncio.create_task(progress_q.get())
        if get_ev in done:
            try:
                ev = get_ev.result()
            except StopAsyncIteration:
                stream_done = True
                get_chunk.cancel()
                try:
                    await get_chunk
                except asyncio.CancelledError:
                    pass
            else:
                yield "ev", ev
                get_ev = asyncio.create_task(aiter.__anext__())

    while True:
        try:
            chunk = progress_q.get_nowait()
            yield "chunk", chunk
        except asyncio.QueueEmpty:
            break


def _runner_input_from_gradio_history(history: list, latest_user_text: str) -> str | list[dict[str, str]]:
    """When SDK session is unavailable, pass full chat as OpenAI-style messages."""
    prior = history[:-1] if history else []
    items: list[dict[str, str]] = []
    for user_msg, bot_msg in prior:
        u = (user_msg or "").strip()
        if u:
            items.append({"role": "user", "content": u})
        if isinstance(bot_msg, str) and bot_msg.strip():
            items.append({"role": "assistant", "content": bot_msg.strip()})
    items.append({"role": "user", "content": latest_user_text.strip()})
    if len(items) == 1:
        return latest_user_text.strip()
    return items


async def chat_respond(message: str, history: list, session: Any):
    text = (message or "").strip()
    if not text:
        yield history, session, ""
        return

    if _USE_SDK_SQLITE_SESSION and session is None:
        session = SQLiteSession(session_id=str(uuid.uuid4()))

    
    history = list(history) + [[text, "_Thinking…_"]]
    yield history, session, ""

    if _USE_SDK_SQLITE_SESSION:
        run_input: str | list = text
        stream_kw: dict = {"session": session, "max_turns": 40}
    else:
        run_input = _runner_input_from_gradio_history(history, text)
        stream_kw = {"max_turns": 40}

    ui_ctx = ResearchUiContext()
    ui_ctx.topic, ui_ctx.prior_qa_block = clarifier_topic_and_prior_from_gradio(history)
    stream_kw["context"] = ui_ctx

    streamed = Runner.run_streamed(
        research_host_agent,
        run_input,
        **stream_kw,
    )

    progress_q: asyncio.Queue[str] = asyncio.Queue()
    set_research_progress_queue(progress_q)
    last_tool_name: str | None = None
    research_live = False
    awaiting_report_after_email = False

    try:
        async for kind, payload in _merge_stream_events_progress(streamed, progress_q):
            if kind == "chunk":
               
                if not research_live:
                    research_live = True
                raw = str(payload)
                s = raw.strip()
                if awaiting_report_after_email:
                    history[-1][1] = raw
                    awaiting_report_after_email = False
                    yield history, session, ""
                    continue
                if s == "Email sent" or s.startswith("Email not sent") or s.startswith("Email skipped"):
                    awaiting_report_after_email = True
                    if s != "Email sent":
                        history[-1][1] = f"_{s}_"
                        yield history, session, ""
                    continue
                history[-1][1] = f"_{s}_"
                yield history, session, ""
                continue

            ev = payload
            if not isinstance(ev, RunItemStreamEvent):
                continue

            if ev.name == "message_output_created" and isinstance(ev.item, MessageOutputItem):
                delta = ItemHelpers.text_message_output(ev.item).strip()
                if not delta:
                    continue
                if research_live:
                    continue
                history[-1][1] = delta
                yield history, session, ""

            elif ev.name == "tool_called":
                last_tool_name = _callable_name(ev.item)
                if last_tool_name == "next_clarifying_question":
                    history[-1][1] = "_Thinking…_"
                    yield history, session, ""
                elif last_tool_name == "run_deep_research":
                    research_live = True

            elif ev.name == "tool_output" and isinstance(ev.item, ToolCallOutputItem):
                if last_tool_name == "run_deep_research":
                    continue
                out = str(ev.item.output)
                if out.strip():
                    history[-1][1] = out
                    yield history, session, ""

    except Exception as exc:
        history[-1][1] = f"_Run error: {exc}_"
        yield history, session, ""
        return
    finally:
        set_research_progress_queue(None)

    if not research_live:
        final = _final_output_to_text(streamed.final_output)
        if final and final.strip():
            history[-1][1] = final
    yield history, session, ""


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown(
        "# Deep Research (agentic)\n\n"
        "1. Send your **research topic** as the first message.\n"
        "2. Answer **three clarifying questions** one at a time.\n"
        "3. The **Research Lead** runs planning, web search, writing, and email.\n\n"
        "**New chat:** use *Clear* to reset the session."
    )
    session_state = gr.State(value=None)
    chatbot = gr.Chatbot(label="Conversation", height=480)
    msg = gr.Textbox(label="Your message", placeholder="Type your topic or answer…", lines=2)
    with gr.Row():
        send = gr.Button("Send", variant="primary")
        clear = gr.Button("Clear")

    msg.submit(
        chat_respond,
        inputs=[msg, chatbot, session_state],
        outputs=[chatbot, session_state, msg],
    )
    send.click(
        chat_respond,
        inputs=[msg, chatbot, session_state],
        outputs=[chatbot, session_state, msg],
    )

    def _reset():
        return [], None, ""

    clear.click(_reset, outputs=[chatbot, session_state, msg])

ui.launch(inbrowser=True)
