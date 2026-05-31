import os
import gradio as gr
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from agents import trace, gen_trace_id

from config import Config
from utils import setup_logging
from services import ImageScannerService
from scanner_agents import (
    VulnerabilityAnalyzerAgent,
    RemediationAdvisorAgent,
    ReportGeneratorAgent,
    EmailAgent,
)

load_dotenv(override=True)

logger = setup_logging()

Config.validate()
scanner = ImageScannerService()
analyzer = VulnerabilityAnalyzerAgent(model=Config.OPENAI_MODEL)
advisor = RemediationAdvisorAgent(model=Config.OPENAI_MODEL)
reporter = ReportGeneratorAgent(model=Config.OPENAI_MODEL)
email_agent = EmailAgent(model=Config.OPENAI_MODEL) if os.getenv("SENDGRID_API_KEY") else None


def _format_final_report(report, trace_url: str) -> str:
    markdown = ReportGeneratorAgent.format_report_markdown(report)
    markdown += f"\n\n---\n\n**OpenAI Trace:** {trace_url}\n"
    return markdown


async def run_scan(image_name: str, min_severity: str):
    Config.MIN_SEVERITY = min_severity
    trace_id = gen_trace_id()

    with trace("Security Scan", trace_id=trace_id):
        try:
            trace_url = f"https://platform.openai.com/traces/{trace_id}"
            yield f"View trace: {trace_url}\n\n"
            yield f"**Starting scan of {image_name}** (Minimum severity: {min_severity})\n\n"

            logger.info(f"Starting UI scan of {image_name} (trace_id: {trace_id})")

            yield "Stage 1: Scanning image with Trivy... (30-120 seconds)\n"
            vulnerabilities = await scanner.scan_image(image_name)
            yield f"Scan complete! Found {len(vulnerabilities)} vulnerabilities\n\n"

            yield "Stage 2: Analyzing vulnerabilities with AI...\n"
            analysis = await analyzer.analyze(vulnerabilities)
            yield f"Analysis complete! {analysis.critical_count} critical, {analysis.high_count} high\n\n"

            yield "Stage 3: Generating remediation plans...\n"
            remediation = await advisor.advise(analysis.analysis)
            yield f"Remediation planning complete! {remediation.total_remediation_plans} plans created\n\n"

            yield "Stage 4: Generating security report...\n"
            report = await reporter.generate_report(image_name, analysis, remediation)
            yield "Report complete!\n\n"

            final_report = _format_final_report(report, trace_url)

            if email_agent:
                yield "Stage 5: Sending report via email...\n"
                try:
                    await email_agent.send_report(final_report)
                    yield "Email sent successfully!\n\n"
                except Exception as e:
                    logger.error(f"Failed to send email: {str(e)}")
                    yield f"Email failed: {str(e)}\n\n"

            yield final_report

            logger.info(f"UI scan complete for {image_name}")
            logger.info(f"OpenAI Trace URL: {trace_url}")

        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            yield f"\n\nError during scan: {str(e)}\n\n"
            yield "Please check:\n"
            yield "- OPENAI_API_KEY is set in .env\n"
            yield "- Trivy is installed (run: which trivy)\n"
            yield "- Docker image name is correct\n"
            raise


with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="red"),
    title="Security Vulnerability Scanner",
) as ui:
    gr.Markdown("# Security Vulnerability Scanner & Remediation Advisor")

    with gr.Row():
        with gr.Column(scale=3):
            image_input = gr.Textbox(
                label="Docker Image",
                placeholder="nginx:latest",
                value="nginx:latest",
            )
        with gr.Column(scale=1):
            severity_dropdown = gr.Dropdown(
                label="Min Severity",
                choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                value="MEDIUM",
            )

    with gr.Row():
        scan_button = gr.Button("Scan Image", variant="primary", scale=1)
        clear_button = gr.Button("Clear", variant="secondary", scale=1)

    report = gr.Markdown(
        label="Report",
        value="Enter an image name and click 'Scan Image' to start...",
    )

    def handle_clear():
        return "Cleared. Enter an image name and click 'Scan Image' to start..."

    scan_button.click(
        fn=run_scan,
        inputs=[image_input, severity_dropdown],
        outputs=report,
    )

    image_input.submit(
        fn=run_scan,
        inputs=[image_input, severity_dropdown],
        outputs=report,
    )

    clear_button.click(fn=handle_clear, outputs=report)


if __name__ == "__main__":
    ui.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
    )
