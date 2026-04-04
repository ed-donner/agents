from functools import wraps
from contextlib import contextmanager
from contextlib import asynccontextmanager
from opentelemetry import trace as otel_trace
from opentelemetry.trace import Status, StatusCode
from openinference.semconv.trace import SpanAttributes

"""
Primary Span Kinds:

CHAIN - Workflow orchestration, multi-step processes
Use for: Sequences of operations, pipelines, complex workflows

AGENT - Agentic behavior with reasoning/planning
Use for: Agent runs, autonomous decision-making

TOOL - Tool/function calls
Use for: Individual tool invocations, function executions

LLM - Large Language Model calls
Use for: Direct LLM API calls (usually auto-set by instrumentation)

RETRIEVER - Retrieval operations
Use for: Vector search, document retrieval, RAG queries

EMBEDDING - Embedding generation
Use for: Text embedding calls, vectorization

RERANKER - Reranking operations
Use for: Result reranking, relevance scoring
"""

# ASYNC CONTEXT MANAGER VERSION
@asynccontextmanager
async def custom_trace(name: str, kind: str = "CHAIN", **attributes):
    """
    Async context manager for tracing workflows with Phoenix-compatible attributes.
    
    Args:
        name: The span/trace name
        kind: OpenInference span kind (CHAIN, AGENT, TOOL, LLM, RETRIEVER, EMBEDDING, RERANKER)
        **attributes: Additional attributes to set on the span
    
    Usage:
        async with custom_trace("Telling a joke", kind="CHAIN", workflow_type="joke"):
            result = await Runner.run(agent, "Tell me a joke")
    """
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
    """
    Sync context manager for tracing (for sync functions).
    
    Usage:
        with custom_trace_sync("get_weather", kind="TOOL", city=city):
            return result
    """
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

# DECORATOR VERSION
def traced_workflow(name: str, kind: str = "CHAIN", **extra_attributes):
    """
    Decorator to trace a workflow with Phoenix-compatible OpenInference attributes.
    
    Args:
        name: The span/trace name
        kind: OpenInference span kind (CHAIN, AGENT, TOOL, LLM, RETRIEVER, EMBEDDING, RERANKER)
        **extra_attributes: Additional attributes to set on the span
    
    Usage:
        @traced_workflow("Telling a joke", kind="CHAIN", workflow_type="joke_generation")
        async def tell_joke(agent, prompt):
            result = await Runner.run(agent, prompt)
            return result
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = otel_trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(name) as span:
                span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, kind)
                
                for key, value in extra_attributes.items():
                    span.set_attribute(key, value)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    
                    if hasattr(result, 'final_output'):
                        span.set_attribute("output.value", str(result.final_output)[:200])
                    
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = otel_trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(name) as span:
                span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, kind)
                
                for key, value in extra_attributes.items():
                    span.set_attribute(key, value)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    
                    if hasattr(result, 'final_output'):
                        span.set_attribute("output.value", str(result.final_output)[:200])
                    
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
