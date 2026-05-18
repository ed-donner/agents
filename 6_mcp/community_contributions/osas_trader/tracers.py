from agents import TracingProcessor, Trace, Span
from database import write_log
import secrets
import string

ALPHANUM = string.ascii_lowercase + string.digits


def make_trace_id(tag: str) -> str:
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = "".join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"


class LogTracer(TracingProcessor):

    def _get_name(self, trace_or_span: Trace | Span) -> str | None:
        trace_id = trace_or_span.trace_id
        name = trace_id.split("_")[1]
        return name.split("0")[0] if "0" in name else None

    def _log(self, trace_or_span, event: str, prefix: str) -> None:
        name = self._get_name(trace_or_span)
        if not name:
            return
        span_data = getattr(trace_or_span, "span_data", None)
        type_ = span_data.type if span_data else "span"
        parts = [prefix]
        if span_data:
            if getattr(span_data, "type", None):
                parts.append(span_data.type)
            if getattr(span_data, "name", None):
                parts.append(span_data.name)
            if getattr(span_data, "server", None):
                parts.append(span_data.server)
        if getattr(trace_or_span, "error", None):
            parts.append(str(trace_or_span.error))
        write_log(name, type_, " ".join(parts))

    def on_trace_start(self, trace) -> None:
        name = self._get_name(trace)
        if name:
            write_log(name, "trace", f"Started: {trace.name}")

    def on_trace_end(self, trace) -> None:
        name = self._get_name(trace)
        if name:
            write_log(name, "trace", f"Ended: {trace.name}")

    def on_span_start(self, span) -> None:
        self._log(span, "start", "Started")

    def on_span_end(self, span) -> None:
        self._log(span, "end", "Ended")

    def force_flush(self) -> None:
        pass

    def shutdown(self) -> None:
        pass
