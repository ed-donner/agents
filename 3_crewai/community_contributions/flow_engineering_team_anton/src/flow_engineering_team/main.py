#!/usr/bin/env python
import json
import sys

from crewai.flow import Flow, listen, start
from pydantic import BaseModel, Field

from .crews.backend_crew.backend_crew import BackendCrew
from .crews.design_crew.design_crew import DesignCrew
from .crews.frontend_crew.frontend_crew import FrontendCrew
from .crews.validation_crew.validation_crew import ValidationCrew
from .sandbox import SANDBOX_ROOT, ensure_sandbox_tree, sandbox_path



app_description = """
    A simple account management system for a trading simulation platform.
    The system should allow users to create an account, deposit funds, and withdraw funds.
    The system should allow users to record that they have bought or sold shares, providing a quantity.
    The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
    The system should be able to report the holdings of the user at any point in time.
    The system should be able to report the profit or loss of the user at any point in time.
    The system should be able to list the transactions that the user has made over time.
    The system should prevent the user from withdrawing funds that would leave them with a negative balance, or
    from buying more shares than they can afford, or selling shares that they don't have.
    The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL
"""

class FlowTriggerError(RuntimeError):
    """Raised when the flow trigger payload cannot be read."""


class AppBuildState(BaseModel):
    app_name: str = "Trading Simulation app"
    app_description: str = app_description 
    target_audience: str = "internal users"
    stack_hint: str = "FastAPI backend and a simple browser UI"
    design_spec: str = ""
    backend_summary: str = ""
    frontend_summary: str = ""
    validation_report: str = ""
    accepted: bool = False
    artifact_files: list[str] = Field(default_factory=list)


class EngineeringAppFlow(Flow[AppBuildState]):
    def _stage_inputs(self) -> dict:
        return {
            "app_name": self.state.app_name,
            "app_description": self.state.app_description,
            "target_audience": self.state.target_audience,
            "stack_hint": self.state.stack_hint,
            "sandbox_root": str(SANDBOX_ROOT),
        }

    def _remember_artifact(self, relative_path: str) -> None:
        artifact_path = sandbox_path(relative_path)
        artifact_name = artifact_path.as_posix()
        if artifact_name not in self.state.artifact_files:
            self.state.artifact_files.append(artifact_name)

    def _write_manifest(self) -> None:
        manifest_path = sandbox_path("flow_manifest.json")
        manifest_path.write_text(
            json.dumps(
                {
                    "app_name": self.state.app_name,
                    "app_description": self.state.app_description,
                    "target_audience": self.state.target_audience,
                    "stack_hint": self.state.stack_hint,
                    "design_spec": self.state.design_spec,
                    "backend_summary": self.state.backend_summary,
                    "frontend_summary": self.state.frontend_summary,
                    "validation_report": self.state.validation_report,
                    "accepted": self.state.accepted,
                    "artifact_files": self.state.artifact_files,
                },
                indent=2,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        self._remember_artifact("flow_manifest.json")

    @start()
    def generate_design(self, crewai_trigger_payload: dict | None = None):
        ensure_sandbox_tree()

        trigger_payload = crewai_trigger_payload or {}
        self.state.app_name = trigger_payload.get("app_name", self.state.app_name)
        self.state.app_description = trigger_payload.get(
            "app_description",
            self.state.app_description,
        )
        self.state.target_audience = trigger_payload.get(
            "target_audience",
            self.state.target_audience,
        )
        self.state.stack_hint = trigger_payload.get("stack_hint", self.state.stack_hint)

        print(f"Designing app: {self.state.app_name}")
        design_result = DesignCrew().crew().kickoff(inputs=self._stage_inputs())
        self.state.design_spec = design_result.raw
        self._remember_artifact("design/design_spec.md")
        self._remember_artifact("design/final_design.md")
        self._write_manifest()

        return {"design_spec": self.state.design_spec}

    @listen(generate_design)
    def implement_app_backend(self, _design_payload):
        print(f"Building backend for: {self.state.app_name}")
        backend_inputs = self._stage_inputs() | {"design_spec": self.state.design_spec}
        backend_result = BackendCrew().crew().kickoff(inputs=backend_inputs)
        self.state.backend_summary = backend_result.raw
        self._remember_artifact("backend/backend_summary.md")
        self._remember_artifact("backend/backend_test_report.md")
        self._write_manifest()

        return {"backend_summary": self.state.backend_summary}

    @listen(implement_app_backend)
    def implement_app_fronend(self, _backend_payload):
        print(f"Building frontend for: {self.state.app_name}")
        frontend_inputs = self._stage_inputs() | {
            "design_spec": self.state.design_spec,
            "backend_summary": self.state.backend_summary,
        }
        frontend_result = FrontendCrew().crew().kickoff(inputs=frontend_inputs)
        self.state.frontend_summary = frontend_result.raw
        self._remember_artifact("frontend/frontend_summary.md")
        self._remember_artifact("frontend/frontend_test_report.md")
        self._write_manifest()

        return {"frontend_summary": self.state.frontend_summary}

    @listen(implement_app_fronend)
    def validate_and_accept_app(self, _frontend_payload):
        print(f"Validating app: {self.state.app_name}")
        validation_inputs = self._stage_inputs() | {
            "design_spec": self.state.design_spec,
            "backend_summary": self.state.backend_summary,
            "frontend_summary": self.state.frontend_summary,
        }
        validation_result = ValidationCrew().crew().kickoff(inputs=validation_inputs)
        self.state.validation_report = validation_result.raw
        normalized_report = validation_result.raw.lower()
        self.state.accepted = (
            "approved" in normalized_report and "revise" not in normalized_report
        )
        self._remember_artifact("validation/integration_review.md")
        self._remember_artifact("validation/signoff.md")
        self._write_manifest()

        print(f"Validation verdict: {'approved' if self.state.accepted else 'revise'}")
        return self.state.validation_report


def kickoff():
    app_flow = EngineeringAppFlow()
    app_flow.kickoff()


def plot():
    app_flow = EngineeringAppFlow()
    app_flow.plot()


def run_with_trigger():
    """
    Run the flow with trigger payload.
    """
    # Get trigger payload from command line argument
    if len(sys.argv) < 2:
        raise FlowTriggerError(
            "No trigger payload provided. Please provide JSON payload as argument."
        )

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        raise FlowTriggerError("Invalid JSON payload provided as argument") from exc

    # Create flow and kickoff with trigger payload.
    # The @start() method will automatically receive crewai_trigger_payload.
    app_flow = EngineeringAppFlow()

    return app_flow.kickoff({"crewai_trigger_payload": trigger_payload})


if __name__ == "__main__":
    kickoff()
