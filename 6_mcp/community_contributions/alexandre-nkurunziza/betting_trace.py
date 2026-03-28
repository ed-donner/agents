from __future__ import annotations

import queue
import threading
from contextlib import contextmanager
from typing import Any

from agents.tracing import default_processor, set_trace_processors
from agents.tracing.processor_interface import TracingProcessor
from agents.tracing.span_data import FunctionSpanData
from agents.tracing.spans import Span
from agents.tracing.traces import Trace


def _clip(text: str, max_len: int = 650) -> str:
    t = " ".join(text.split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


_ROLE_PREFIX: dict[str, str] = {
    "researcher": "**Researcher:** Here’s what we pulled from the demo market — ",
    "analyst": "**Analyst:** Our read and suggestion — ",
    "decision": "**Betting:** ",
}


class TraceLineBuffer:
    def __init__(self) -> None:
        self._q: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._lines: list[str] = []

    def push(self, line: str) -> None:
        with self._lock:
            self._lines.append(line)
        self._q.put(line)

    def snapshot_markdown(self) -> str:
        with self._lock:
            lines = list(self._lines)
        if not lines:
            return "_Getting ready…_"
        return "## What happened\n\n" + "\n".join(lines)

    def drain_queue_nowait(self) -> list[str]:
        out: list[str] = []
        while True:
            try:
                out.append(self._q.get_nowait())
            except queue.Empty:
                break
        return out

    def clear(self) -> None:
        with self._lock:
            self._lines.clear()
        while True:
            try:
                self._q.get_nowait()
            except queue.Empty:
                break


class LiveTraceProcessor(TracingProcessor):
    def __init__(self, buf: TraceLineBuffer) -> None:
        self._buf = buf

    def on_trace_start(self, trace: Trace) -> None:
        pass

    def on_trace_end(self, trace: Trace) -> None:
        pass

    def on_span_start(self, span: Span[Any]) -> None:
        pass

    def on_span_end(self, span: Span[Any]) -> None:
        line = business_line_from_span(span)
        if line:
            self._buf.push(line)

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass


def business_line_from_span(span: Span[Any]) -> str | None:
    sd = span.span_data
    if not isinstance(sd, FunctionSpanData):
        return None
    key = (sd.name or "").strip().lower()
    prefix = _ROLE_PREFIX.get(key)
    if not prefix:
        return None
    err = span.error
    body = _clip(str(sd.output) if sd.output is not None else "")
    if err:
        return f"{prefix}(Could not complete: {err['message']})"
    if key == "decision":
        return f"{prefix}{body}"
    return f"{prefix}{body}"


@contextmanager
def live_trace_session(buf: TraceLineBuffer):
    proc = LiveTraceProcessor(buf)
    set_trace_processors([default_processor(), proc])
    try:
        yield
    finally:
        set_trace_processors([default_processor()])
