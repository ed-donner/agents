from agents import TracingProcessor
from src.database.database import write_log
from datetime import datetime
import uuid

class LogTracer(TracingProcessor):
    def __init__(self):
        pass

    def on_trace_start(self, trace):
        trace_id = trace.trace_id if hasattr(trace, 'trace_id') else str(trace)
        trader_name = trace_id.replace('trace_', '').split('_')[1] if 'trace_' in trace_id else trace_id.split('-')[0]
        write_log(trader_name, "trace", f"Started")

    def on_trace_end(self, trace):
        trace_id = trace.trace_id if hasattr(trace, 'trace_id') else str(trace)
        trader_name = trace_id.replace('trace_', '').split('_')[1] if 'trace_' in trace_id else trace_id.split('-')[0]
        write_log(trader_name, "trace", f"Completed")

    def on_span_start(self, span):
        trace_id = span.trace_id if hasattr(span, 'trace_id') else ""
        trader_name = trace_id.replace('trace_', '').split('_')[1] if 'trace_' in trace_id and '_' in trace_id else "system"

        name = span.name if hasattr(span, 'name') else ""

        if "agent" in name.lower():
            write_log(trader_name, "agent", f"{name}")
        elif "tool" in name.lower() or "function" in name.lower():
            write_log(trader_name, "function", f"{name}")
        elif "generation" in name.lower() or "llm" in name.lower():
            write_log(trader_name, "generation", "Thinking...")

    def on_span_end(self, span):
        pass

    def force_flush(self):
        pass

    def shutdown(self):
        pass

def make_trace_id(trader_name: str) -> str:
    unique_id = str(uuid.uuid4())[:8]
    return f"trace_{trader_name.lower()}_{unique_id}"
