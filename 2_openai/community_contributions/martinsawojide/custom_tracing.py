from functools import wraps
from contextlib import contextmanager
from contextlib import asynccontextmanager
from opentelemetry import trace as otel_trace
from opentelemetry.trace import Status, StatusCode
from openinference.semconv.trace import SpanAttributes

@asynccontextmanager
async def custom_trace(name: str, kind: str = "CHAIN", **attributes):
    """Async context manager for tracing workflows with Phoenix-compatible attributes"""
    tracer = otel_trace.get_tracer(__name__)
    
    with tracer.start_as_current_span(name) as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, kind)
        
        for key, value in attributes.items():
            span.set_attribute(key, value)
        
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

@contextmanager
def custom_trace_sync(name: str, kind: str = "CHAIN", **attributes):
    """Sync context manager for tracing (for sync functions)"""
    
    tracer = otel_trace.get_tracer(__name__)
    
    with tracer.start_as_current_span(name) as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, kind)
        
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
