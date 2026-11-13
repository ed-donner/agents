import time
from typing import Any

from pydantic import BaseModel, Field
from crewai.flow import Flow, listen, start
from crewai.telemetry.tracing.last_run import read_last_run

from product_factory.crew import ProductFactory
from product_factory.tools.sandbox_reset import (
    _reset_workstream,
    workstream_lock,
    workstream_root,
)
from product_factory.tools.verdict import QualityVerdict
from product_factory.trace import latest_trace_url


# One crew pass keeps runs tight. Raise to 2–3 only when you want automatic
# fix-and-retry after a failed quality verdict.
MAX_QUALITY_CYCLES = 1
DEFAULT_REQUIREMENTS = "Build a small, useful Python product with a Gradio interface."


class Workstream(BaseModel):
    id: str = "main"
    requirements: str = DEFAULT_REQUIREMENTS
    feedback: list[str] = Field(default_factory=list)


class FactoryState(BaseModel):
    workstreams: list[Workstream] = Field(default_factory=list)
    results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    trace_link: str = ""
    previous_execution_id: str | None = None


def _with_feedback(requirements: str, feedback: list[str], round_number: int) -> str:
    items = "\n".join(f"- {item}" for item in feedback)
    return f"{requirements}\n\n## Follow-up feedback (round {round_number})\n{items}"


class ProductFactoryFlow(Flow[FactoryState]):
    @start()
    def load_workstreams(self) -> list[str]:
        previous_record = read_last_run() or {}
        self.state.previous_execution_id = previous_record.get("execution_id")
        if not self.state.workstreams:
            self.state.workstreams = [Workstream()]
        return [workstream.id for workstream in self.state.workstreams]

    @listen(load_workstreams)
    def run_workstreams(self, _loaded: list[str]) -> dict[str, dict[str, Any]]:
        for workstream in self.state.workstreams:
            self._run_workstream(workstream)
        return self.state.results

    def _run_workstream(self, workstream: Workstream) -> None:
        root = workstream_root(workstream.id)
        root.mkdir(parents=True, exist_ok=True)
        requirements = workstream.requirements
        feedback_round = 0
        for feedback in workstream.feedback:
            feedback_round += 1
            requirements = _with_feedback(requirements, [feedback], feedback_round)

        factory = ProductFactory(workstream.id)
        design = factory.engineering_lead().kickoff(
            "Produce a design of at most 250 lines for the following requirements. "
            "Assign concrete backend, frontend, and test responsibilities. Do not "
            f"write files or use tools.\n\n{requirements}"
        ).raw
        (root / "design.md").write_text(design, encoding="utf-8")

        verdict = QualityVerdict(passed=False, fixes=["No quality cycle ran."])
        cycles = 0
        for cycle in range(1, MAX_QUALITY_CYCLES + 1):
            cycles = cycle
            if cycle > 1:
                feedback_round += 1
                requirements = _with_feedback(
                    requirements, verdict.fixes, feedback_round
                )
            output = (
                ProductFactory(workstream.id)
                .crew()
                .kickoff(
                    inputs={
                        "workstream_id": workstream.id,
                        "requirements": requirements,
                        "design": design,
                    }
                )
            )
            if output.pydantic is None:
                raise RuntimeError("Quality task returned no QualityVerdict.")
            verdict = QualityVerdict.model_validate(output.pydantic)
            if verdict.passed:
                break

        self.state.results[workstream.id] = {
            "status": "passed" if verdict.passed else "max cycles reached",
            "passed": verdict.passed,
            "cycles": cycles,
            "fixes": verdict.fixes,
            "evidence": verdict.evidence,
        }

    @listen(run_workstreams)
    def summarize(self, results: dict[str, dict[str, Any]]) -> dict[str, Any]:
        self.state.trace_link = (
            latest_trace_url(self.state.previous_execution_id) or ""
        )
        return {"verdicts": results, "trace_link": self.state.trace_link or None}


def run_flow(
    workstream_id: str = "main",
    requirements: str = DEFAULT_REQUIREMENTS,
    feedback: str = "",
    reset: bool = False,
) -> dict[str, Any]:
    root = workstream_root(workstream_id)
    with workstream_lock(root):
        if reset:
            _reset_workstream(root)
        flow = ProductFactoryFlow(tracing=True)
        result = flow.kickoff(
            inputs={
                "workstreams": [
                    {
                        "id": workstream_id,
                        "requirements": requirements,
                        "feedback": [feedback] if feedback.strip() else [],
                    }
                ]
            }
        )
        if result["trace_link"] is None:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                time.sleep(0.25)
                trace_link = latest_trace_url(flow.state.previous_execution_id)
                if trace_link:
                    result["trace_link"] = trace_link
                    flow.state.trace_link = trace_link
                    break
        return result
