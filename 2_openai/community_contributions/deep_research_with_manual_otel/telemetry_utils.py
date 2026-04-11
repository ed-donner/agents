import time
from opentelemetry import trace

tracer = trace.get_tracer("llm")

async def traced_llm_call(model: str, prompt: str, call_fn):
    start = time.time()

    with tracer.start_as_current_span(f"llm.openai.request") as span:
        span.set_attribute("llm.vendor", "openai")
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.input.length", len(prompt))
        span.set_attribute("llm.input.preview", prompt[:200])

        try:
            response = await call_fn()
        except Exception as e:
            span.set_attribute("llm.error", True)
            span.set_attribute("llm.error.message", str(e))
            raise

        duration = time.time() - start
        span.set_attribute("llm.duration_ms", int(duration * 1000))

        # If the OpenAI response includes token usage
        if hasattr(response, "usage"):
            span.set_attribute("llm.tokens.prompt", response.usage.prompt_tokens)
            span.set_attribute("llm.tokens.completion", response.usage.completion_tokens)
            span.set_attribute("llm.tokens.total", response.usage.total_tokens)

        return response
