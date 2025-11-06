from openai.types.beta import tracing
from database import write_log

class LogTracer:
    def on_span_start(self, span: tracing.Span):
        write_log("agent", "DEBUG", f"start: {span.type}:{span.name}")
    def on_span_end(self, span: tracing.Span):
        write_log("agent", "DEBUG", f"end: {span.type}:{span.name} status={span.status}")