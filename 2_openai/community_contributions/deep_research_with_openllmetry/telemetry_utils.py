from opentelemetry import trace
import asyncio
import os

tracer = trace.get_tracer("llm")

async def traced_llm_call(model: str, prompt: str, call_fn):
    
    with tracer.start_as_current_span("llm.request") as span:
        
        span.set_attribute("gen_ai.system", "openai")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.operation.name", "chat")
            
        # 2. Execute actual agent logic
        return await call_fn()

