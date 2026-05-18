from doctest import debug
from pickle import TRUE
from traceloop.sdk import Traceloop
import os

from agents.tracing import provider
import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

import time
load_dotenv(override=True)

# -------------------------------
# Enable Traceloop OpenLLMetry
# -------------------------------
api_token = os.getenv("TRACELOOP_API_KEY")
api_endpoint = os.getenv("TRACELOOP_BASE_URL")
os.environ["OTEL_METRICS_EXPORTER"] = "otlp"
os.environ["OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE"] = "delta"
headers = {"Authorization": f"Api-Token {api_token}"}
Traceloop.init(
    app_name=os.getenv("OTEL_SERVICE_NAME", "deep-research-ui"),
    api_endpoint=api_endpoint,
    headers=headers,
    should_enrich_metrics=True)

# Configure OpenTelemetry traces (exports to OTLP HTTP, defaults to localhost:4318).
resource = Resource.create(
    {
        "service.name": os.getenv("OTEL_SERVICE_NAME", "deep-research-ui"),
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("APP_ENV", "dev")
    }
)

# -------------------------------
# Research pipeline
# -------------------------------
async def run(query: str):
    #with tracer.start_as_current_span("deep_research.run")as span:
    #    span.set_attribute("query.length", len(query))
    #    span.set_attribute("query.preview", query[:200])

        async for chunk in ResearchManager().run(query):
            yield chunk

# -------------------------------
# UI
# -------------------------------
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

#with tracer.start_as_current_span("deep_research.ui_launch"):
    ui.launch(inbrowser=True)

