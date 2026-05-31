import secrets
import string
from datetime import datetime
from typing import Optional

try:
    from agents import TracingProcessor, Trace, Span, add_trace_processor
except ImportError:
    TracingProcessor = None
    Trace = None
    Span = None


def make_trace_id(agent_name: str = "trace") -> str:
    tag = f"{agent_name.lower()}0"
    prefix_len = 6
    max_len = 38
    remaining = max_len - prefix_len - len(tag)
    if remaining <= 0:
        max_tag_len = max_len - prefix_len - 5
        tag = f"{agent_name.lower()[:max_tag_len]}0"
        remaining = 5
    chars = string.ascii_lowercase + string.digits
    random_suffix = ''.join(secrets.choice(chars) for _ in range(remaining))
    return f"trace_{tag}{random_suffix}"


class SimpleTracer:
    def __init__(self, name: str, trace_id: str = None):
        self.name = name
        self.trace_id = trace_id or make_trace_id()
        self.start_time = datetime.now()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class DevOpsLogTracer:
    def shutdown(self):
        pass

    def get_agent_name(self, trace_or_span) -> Optional[str]:
        try:
            trace_id = trace_or_span.trace_id
            if not trace_id.startswith("trace_"):
                return None
            name_part = trace_id[6:]
            if '0' in name_part:
                return name_part.split('0')[0]
            return None
        except Exception:
            return None

    def on_trace_start(self, trace) -> None:
        pass

    def on_trace_end(self, trace) -> None:
        pass

    def on_span_start(self, span) -> None:
        pass

    def on_span_end(self, span) -> None:
        pass


def register_tracer():
    try:
        tracer = DevOpsLogTracer()
        if TracingProcessor is not None and add_trace_processor is not None:
            add_trace_processor(tracer)
        return tracer
    except ImportError:
        return None


def trace(name: str, trace_id: str = None):
    try:
        from agents import trace as agents_trace
        return agents_trace(name, trace_id=trace_id)
    except ImportError:
        return SimpleTracer(name, trace_id)
