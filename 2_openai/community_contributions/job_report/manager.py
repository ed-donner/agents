import os
import tempfile
from pathlib import Path

from agents import Runner, gen_trace_id, trace

from job_report.company_research import company_research_agent
from job_report.summarizer import summarizer_agent
from job_report.technical_research import technical_research_agent


class Manager:
    """Runs company research, technical research, then summarizer (PDF) in sequence."""

    async def run(self, job_description: str, company_name: str = "") -> tuple[str, str | None]:
        job_description = (job_description or "").strip()
        if not job_description:
            return "Please paste a job description.", None

        parts: list[str] = []
        trace_id = gen_trace_id()
        with trace("Job report", trace_id=trace_id):
            parts.append(
                f"**Trace:** [OpenAI trace](https://platform.openai.com/traces/trace?trace_id={trace_id})\n"
            )

            parts.append("## 1. Technical research\n\n_Running technical research agent…_\n")
            tech_result = await Runner.run(
                technical_research_agent,
                f"Job description:\n\n{job_description}\n",
            )
            tech_report = str(tech_result.final_output)
            parts.append(tech_report)

            parts.append("\n## 2. Company research\n\n_Running company research agent…_\n")
            if (company_name or "").strip():
                company_prompt = (
                    f"Company to research: {company_name.strip()}\n\n"
                    f"Job description for context:\n\n{job_description}\n"
                )
            else:
                company_prompt = (
                    f"Job description:\n\n{job_description}\n\n"
                    "Identify the hiring company from this job description. "
                    "Then research that company and produce the report requested in your instructions."
                )
            company_result = await Runner.run(company_research_agent, company_prompt)
            company_report = str(company_result.final_output)
            parts.append(company_report)

            session_dir = Path(tempfile.mkdtemp())
            os.environ["JOB_REPORT_OUTPUT_DIR"] = str(session_dir)
            try:
                parts.append("\n## 3. Summary & PDF\n\n_Running summarizer agent…_\n")
                summary_input = (
                    f"Job description:\n\n{job_description}\n\n"
                    f" Company research report \n{company_report}\n\n"
                    f"Technical research report \n{tech_report}\n\n"
                    "Using the above, produce the cheatsheet described in your instructions. "
                    "When complete, call write_job_report_pdf with the full cheatsheet text so it is saved as job_report.pdf."
                )
                summary_result = await Runner.run(summarizer_agent, summary_input)
                parts.append(str(summary_result.final_output))
            finally:
                os.environ.pop("JOB_REPORT_OUTPUT_DIR", None)

            pdf_path = session_dir / "job_report.pdf"
            pdf_str = str(pdf_path) if pdf_path.is_file() else None
            if pdf_path.is_file():
                parts.append(f"\n**PDF:** `{pdf_path}`")
            else:
                parts.append("\n_PDF was not created; check summarizer/tool errors above._")

        return "\n".join(parts), pdf_str