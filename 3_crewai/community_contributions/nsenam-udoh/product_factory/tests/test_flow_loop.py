import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from crewai import Process

from product_factory.crew import ProductFactory
from product_factory.flow import ProductFactoryFlow
from product_factory.tools.verdict import QualityVerdict


def verdict(passed: bool, fixes: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        pydantic=QualityVerdict(
            passed=passed,
            fixes=fixes or [],
            evidence=["test exit code 0"] if passed else [],
        )
    )


def factory_mock(crew_results: list[SimpleNamespace]) -> tuple[MagicMock, MagicMock]:
    factory = MagicMock()
    factory.engineering_lead.return_value.kickoff.return_value.raw = "# Design"
    crew = MagicMock()
    crew.kickoff.side_effect = crew_results
    factory.crew.return_value = crew
    return factory, crew


class QualityLoopTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temporary.cleanup()

    def run_flow(self, crew_results: list[SimpleNamespace]):
        factory, crew = factory_mock(crew_results)
        flow = ProductFactoryFlow()
        flow.load_workstreams()
        with (
            patch("product_factory.flow.ProductFactory", return_value=factory),
            patch(
                "product_factory.flow.workstream_root",
                return_value=Path(self.temporary.name) / "main",
            ),
        ):
            results = flow.run_workstreams([])
        return results["main"], crew, flow

    def test_quality_loop_stops_at_max_cycles(self):
        from product_factory.flow import MAX_QUALITY_CYCLES

        result, crew, _ = self.run_flow(
            [verdict(False, ["fix backend"]) for _ in range(MAX_QUALITY_CYCLES)]
        )
        self.assertEqual(crew.kickoff.call_count, MAX_QUALITY_CYCLES)
        self.assertEqual(result["cycles"], MAX_QUALITY_CYCLES)
        self.assertEqual(result["status"], "max cycles reached")
        self.assertEqual(result["fixes"], ["fix backend"])
        if MAX_QUALITY_CYCLES > 1:
            last_inputs = crew.kickoff.call_args_list[-1].kwargs["inputs"]
            self.assertIn("## Follow-up feedback", last_inputs["requirements"])
            self.assertIn("- fix backend", last_inputs["requirements"])

    def test_quality_loop_stops_as_soon_as_verdict_passes(self):
        from product_factory.flow import MAX_QUALITY_CYCLES

        if MAX_QUALITY_CYCLES == 1:
            result, crew, _ = self.run_flow([verdict(True)])
            self.assertEqual(crew.kickoff.call_count, 1)
            self.assertEqual(result["cycles"], 1)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["evidence"], ["test exit code 0"])
            return

        result, crew, _ = self.run_flow(
            [verdict(False, ["add validation"]), verdict(True)]
        )
        self.assertEqual(crew.kickoff.call_count, 2)
        self.assertEqual(result["cycles"], 2)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["evidence"], ["test exit code 0"])
        second_inputs = crew.kickoff.call_args_list[1].kwargs["inputs"]
        self.assertIn("## Follow-up feedback (round 1)", second_inputs["requirements"])
        self.assertIn("- add validation", second_inputs["requirements"])

    def test_design_is_written_before_crew_runs(self):
        _, crew, flow = self.run_flow([verdict(True)])
        design = Path(self.temporary.name) / "main" / "design.md"
        self.assertEqual(design.read_text(encoding="utf-8"), "# Design")
        inputs = crew.kickoff.call_args.kwargs["inputs"]
        self.assertEqual(inputs["design"], "# Design")
        self.assertEqual(flow.state.results["main"]["cycles"], 1)


class ConstructionTests(unittest.TestCase):
    def test_crew_is_hierarchical_with_four_specialists(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            try:
                os.chdir(temporary)
                crew = ProductFactory().crew()
            finally:
                os.chdir(previous)
        self.assertEqual(crew.process, Process.hierarchical)
        self.assertIsNotNone(crew.manager_agent)
        self.assertEqual(len(crew.agents), 4)
        self.assertEqual(len(crew.tasks), 4)
        self.assertNotIn(crew.manager_agent, crew.agents)
        self.assertTrue(crew.tracing)
        iteration_limits = {agent.role: agent.max_iter for agent in crew.agents}
        self.assertEqual(
            iteration_limits,
            {
                "Backend Python engineer": 8,
                "Gradio frontend engineer": 8,
                "Python test engineer": 10,
                "Independent software quality inspector": 10,
            },
        )
        self.assertEqual(crew.manager_agent.max_iter, 10)
        inspector = next(
            agent
            for agent in crew.agents
            if agent.role == "Independent software quality inspector"
        )
        self.assertEqual(
            {item.name for item in inspector.tools},
            {
                "check_sandbox_app",
                "list_sandbox_files",
                "read_sandbox_file",
                "run_sandbox_python",
            },
        )

    def test_task_prompt_requires_complete_report(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            try:
                os.chdir(temporary)
                crew = ProductFactory().crew()
            finally:
                os.chdir(previous)
        backend_task = crew.tasks[0]
        prompt = backend_task.prompt()
        self.assertNotIn("not a summary", prompt)
        self.assertIn(
            "The final answer must be the complete report described above, with every named part.",
            prompt,
        )
        self.assertIn(backend_task.expected_output, prompt)

    def test_ui_builds_without_launching(self):
        import app
        import gradio as gr

        self.assertIsInstance(app.build_ui(), gr.Blocks)
        with patch("app.reset_workstream") as reset:
            status, _, _ = app._reset("main", False)
        reset.assert_not_called()
        self.assertIn("Reset not run", status)


if __name__ == "__main__":
    unittest.main()
