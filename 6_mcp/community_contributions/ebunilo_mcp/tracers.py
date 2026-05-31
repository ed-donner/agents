import secrets
import string

from agents import Span, Trace, TracingProcessor

from database import write_log

ALPHANUM = string.ascii_lowercase + string.digits


def make_trace_id(tag: str) -> str:
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = "".join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"


class LogTracer(TracingProcessor):
    def get_name(self, trace_or_span: Trace | Span) -> str | None:
        trace_id = trace_or_span.trace_id
        name = trace_id.split("_")[1]
        if "0" in name:
            return name.split("0")[0]
        return None

    def on_trace_start(self, trace) -> None:
        name = self.get_name(trace)
        if name:
            write_log(name, "trace", f"Started: {trace.name}")

    def on_trace_end(self, trace) -> None:
        name = self.get_name(trace)
        if name:
            write_log(name, "trace", f"Ended: {trace.name}")

    def on_span_start(self, span) -> None:
        name = self.get_name(span)
        type = span.span_data.type if span.span_data else "span"
        if name:
            message = "Started"
            if span.span_data:
                if span.span_data.type:
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
                if hasattr(span.span_data, "server") and span.span_data.server:
                    message += f" {span.span_data.server}"
            if span.error:
                message += f" {span.error}"
            write_log(name, type, message)

    def on_span_end(self, span) -> None:
        name = self.get_name(span)
        type = span.span_data.type if span.span_data else "span"
        if name:
            message = "Ended"
            if span.span_data:
                if span.span_data.type:
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
                if hasattr(span.span_data, "server") and span.span_data.server:
                    message += f" {span.span_data.server}"
            if span.error:
                message += f" {span.error}"
            write_log(name, type, message)

    def force_flush(self) -> None:
        pass

    def shutdown(self) -> None:
        pass
