import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import os
import time

load_dotenv(override=True)

# Configure OpenTelemetry traces (exports to OTLP HTTP, defaults to localhost:4318).
resource = Resource.create(
    {
        "service.name": os.getenv("OTEL_SERVICE_NAME", "deep-research-ui"),
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("APP_ENV", "dev")
    }
)
provider = TracerProvider(resource=resource)
#otlp_endpoint = "http://localhost:4318"

provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# ---- LLM tracing helper ----
async def traced_llm_call(model: str, prompt: str, call_fn):
    start = time.time()

    with tracer.start_as_current_span("llm.openai.request") as span:
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

        if hasattr(response, "usage"):
            span.set_attribute("llm.tokens.prompt", response.usage.prompt_tokens)
            span.set_attribute("llm.tokens.completion", response.usage.completion_tokens)
            span.set_attribute("llm.tokens.total", response.usage.total_tokens)

        return response


async def run(query: str):
    with tracer.start_as_current_span("deep_research.run")as span:
        span.set_attribute("query.length", len(query))
        span.set_attribute("query.preview", query[:200])

        async for chunk in ResearchManager().run(query):
            yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

with tracer.start_as_current_span("deep_research.ui_launch"):
    ui.launch(inbrowser=True)

