"""
Unit tests for MedScribe AI.
Tests all modules without hitting the live API (using mocks).
Run with: python -m pytest tests/ -v
"""

import json
import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Config tests ─────────────────────────────────────────────────────────────

class TestConfig(unittest.TestCase):

    def test_get_model_default(self):
        from src.config import get_model
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_MODEL", None)
            model = get_model()
        self.assertIsInstance(model, str)
        self.assertGreater(len(model), 0)

    def test_get_openrouter_key_raises_when_missing(self):
        from src.config import get_openrouter_key
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                get_openrouter_key()

    def test_get_openrouter_key_raises_on_placeholder(self):
        from src.config import get_openrouter_key
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "your_openrouter_api_key_here"}):
            with self.assertRaises(ValueError):
                get_openrouter_key()

    def test_is_debug_false_by_default(self):
        from src.config import is_debug
        with patch.dict(os.environ, {"FLASK_DEBUG": "false"}):
            self.assertFalse(is_debug())

    def test_is_debug_true(self):
        from src.config import is_debug
        with patch.dict(os.environ, {"FLASK_DEBUG": "true"}):
            self.assertTrue(is_debug())


# ── LLM client tests ──────────────────────────────────────────────────────────

class TestLLMClient(unittest.TestCase):

    @patch("src.utils.llm_client.requests.post")
    @patch("src.utils.llm_client.get_openrouter_key", return_value="test-key")
    def test_call_llm_returns_content(self, mock_key, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "  Hello from LLM  "}}]
        }
        mock_post.return_value = mock_response

        from src.utils.llm_client import call_llm
        result = call_llm("system", "user")
        self.assertEqual(result, "Hello from LLM")

    @patch("src.utils.llm_client.requests.post")
    @patch("src.utils.llm_client.get_openrouter_key", return_value="test-key")
    def test_call_llm_raises_on_bad_structure(self, mock_key, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "structure"}
        mock_post.return_value = mock_response

        from src.utils.llm_client import call_llm
        with self.assertRaises(RuntimeError):
            call_llm("system", "user")


# ── File writer tests ─────────────────────────────────────────────────────────

class TestFileWriter(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())

    def test_write_and_read_file(self):
        from src.utils.file_writer import write_file
        path = write_file(self.tmp, "test.txt", "hello world")
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(), "hello world")

    def test_make_run_id_format(self):
        from src.utils.file_writer import make_run_id
        run_id = make_run_id("PT-001")
        self.assertIn("PT", run_id)
        self.assertIn("001", run_id)
        # Should contain timestamp portion
        self.assertGreater(len(run_id), 10)

    def test_make_run_id_sanitises_special_chars(self):
        from src.utils.file_writer import make_run_id
        run_id = make_run_id("PT/001 test!")
        self.assertNotIn("/", run_id)
        self.assertNotIn(" ", run_id)
        self.assertNotIn("!", run_id)

    def test_extract_code_blocks_single(self):
        from src.utils.file_writer import extract_code_blocks
        text = "Here is code:\n```python filename: foo.py\nprint('hi')\n```\nDone."
        blocks = extract_code_blocks(text)
        self.assertIn("foo.py", blocks)
        self.assertEqual(blocks["foo.py"], "print('hi')")

    def test_extract_code_blocks_multiple(self):
        from src.utils.file_writer import extract_code_blocks
        text = (
            "```python filename: a.py\nx = 1\n```\n"
            "```python filename: b.py\ny = 2\n```"
        )
        blocks = extract_code_blocks(text)
        self.assertEqual(len(blocks), 2)
        self.assertIn("a.py", blocks)
        self.assertIn("b.py", blocks)

    def test_extract_code_blocks_empty(self):
        from src.utils.file_writer import extract_code_blocks
        blocks = extract_code_blocks("No code here.")
        self.assertEqual(blocks, {})


# ── Task runner tests ─────────────────────────────────────────────────────────

class TestTaskRunner(unittest.TestCase):

    def test_run_task_success(self):
        from src.tasks.task_runner import run_task
        result = run_task("TestTask", "TestAgent", lambda x: f"done:{x}", "input")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "done:input")
        self.assertEqual(result.task_name, "TestTask")

    def test_run_task_failure(self):
        from src.tasks.task_runner import run_task
        def bad_fn():
            raise ValueError("something broke")
        result = run_task("BadTask", "BadAgent", bad_fn)
        self.assertFalse(result.success)
        self.assertIn("something broke", result.error)
        self.assertEqual(result.output, "")

    def test_run_task_captures_exception_type(self):
        from src.tasks.task_runner import run_task
        result = run_task("T", "A", lambda: (_ for _ in ()).throw(RuntimeError("oops")))
        self.assertFalse(result.success)
        self.assertIn("oops", result.error)


# ── Agent prompt tests ────────────────────────────────────────────────────────

class TestAgentPrompts(unittest.TestCase):
    """Verify each agent calls the LLM with correct arguments."""

    @patch("src.agents.clinical_analyst.call_llm", return_value='{"patient_id": "P1"}')
    def test_clinical_analyst_calls_llm(self, mock_llm):
        from src.agents.clinical_analyst import run
        result = run("patient notes here")
        mock_llm.assert_called_once()
        args = mock_llm.call_args
        self.assertIn("patient notes here", args[1]["user_prompt"] if args[1] else args[0][1])

    @patch("src.agents.discharge_planner.call_llm", return_value='{"discharge_condition": "Stable"}')
    def test_discharge_planner_calls_llm(self, mock_llm):
        from src.agents.discharge_planner import run
        run('{"patient_id": "P1"}')
        mock_llm.assert_called_once()

    @patch("src.agents.medical_writer.call_llm", return_value="DISCHARGE SUMMARY\n===")
    def test_medical_writer_calls_llm(self, mock_llm):
        from src.agents.medical_writer import run
        result = run('{"patient_id": "P1"}', '{"discharge_condition": "Stable"}')
        mock_llm.assert_called_once()
        self.assertEqual(result, "DISCHARGE SUMMARY\n===")

    @patch("src.agents.qa_reviewer.call_llm", return_value='{"approved": true, "quality_score": 90}')
    def test_qa_reviewer_calls_llm(self, mock_llm):
        from src.agents.qa_reviewer import run
        run("some discharge summary text")
        mock_llm.assert_called_once()

    @patch("src.agents.code_engineer.call_llm", return_value="```python filename: foo.py\npass\n```")
    def test_code_engineer_calls_llm(self, mock_llm):
        from src.agents.code_engineer import run
        result = run("{}", "summary text", "{}")
        mock_llm.assert_called_once()
        self.assertIn("foo.py", result)


# ── Crew orchestrator tests ───────────────────────────────────────────────────

class TestCrew(unittest.TestCase):

    def _mock_agents(self):
        """Return patch targets for all five agent run() functions."""
        return {
            "src.crew.clinical_analyst.run":  '{"patient_id": "P1", "patient_name": "Test"}',
            "src.crew.discharge_planner.run": '{"discharge_condition": "Stable", "discharge_medications": []}',
            "src.crew.medical_writer.run":    "DISCHARGE SUMMARY\n===\n\nPATIENT INFORMATION\nTest patient",
            "src.crew.qa_reviewer.run":       '{"approved": true, "quality_score": 88, "issues_found": []}',
            "src.crew.code_engineer.run":     "```python filename: discharge_generator.py\npass\n```",
        }

    def test_crew_success_pipeline(self):
        from src.crew import run_crew
        patches = self._mock_agents()
        with patch("src.crew.clinical_analyst.run",  return_value=patches["src.crew.clinical_analyst.run"]), \
             patch("src.crew.discharge_planner.run", return_value=patches["src.crew.discharge_planner.run"]), \
             patch("src.crew.medical_writer.run",    return_value=patches["src.crew.medical_writer.run"]), \
             patch("src.crew.qa_reviewer.run",       return_value=patches["src.crew.qa_reviewer.run"]), \
             patch("src.crew.code_engineer.run",     return_value=patches["src.crew.code_engineer.run"]):
            result = run_crew("Full patient notes with enough detail to process.", "TEST-PT")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["tasks"]), 5)
        self.assertTrue(all(t["success"] for t in result["tasks"]))
        self.assertGreater(len(result["files"]), 0)
        self.assertEqual(result["qa_score"], 88)
        self.assertTrue(result["qa_approved"])

    def test_crew_aborts_on_first_failure(self):
        from src.crew import run_crew
        with patch("src.crew.clinical_analyst.run", side_effect=RuntimeError("LLM timeout")):
            result = run_crew("some notes", "FAIL-PT")

        self.assertFalse(result["success"])
        self.assertEqual(len(result["tasks"]), 1)
        self.assertFalse(result["tasks"][0]["success"])

    def test_crew_run_id_contains_patient_id(self):
        from src.crew import run_crew
        patches = self._mock_agents()
        with patch("src.crew.clinical_analyst.run",  return_value=patches["src.crew.clinical_analyst.run"]), \
             patch("src.crew.discharge_planner.run", return_value=patches["src.crew.discharge_planner.run"]), \
             patch("src.crew.medical_writer.run",    return_value=patches["src.crew.medical_writer.run"]), \
             patch("src.crew.qa_reviewer.run",       return_value=patches["src.crew.qa_reviewer.run"]), \
             patch("src.crew.code_engineer.run",     return_value=patches["src.crew.code_engineer.run"]):
            result = run_crew("Patient notes here.", "MYPATIENT")

        self.assertIn("MYPATIENT", result["run_id"])


# ── Flask API tests ───────────────────────────────────────────────────────────

class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        import importlib
        import src.config
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "FLASK_SECRET_KEY": "test"}):
            import app as flask_app
            flask_app.app.config["TESTING"] = True
            self.client = flask_app.app.test_client()
            self._jobs = flask_app._jobs

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "ok")

    def test_index_returns_html(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"MedScribe", res.data)

    def test_submit_missing_data(self):
        res = self.client.post("/api/submit",
            data=json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_submit_too_short(self):
        res = self.client.post("/api/submit",
            data=json.dumps({"patient_data": "short"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_submit_valid_starts_job(self):
        long_notes = "Patient " + "X" * 100
        res = self.client.post("/api/submit",
            data=json.dumps({"patient_data": long_notes, "patient_id": "TEST"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "running")

    def test_status_unknown_job(self):
        res = self.client.get("/api/status/nonexistent-job-id")
        self.assertEqual(res.status_code, 404)

    def test_status_running_job(self):
        import app as flask_app
        flask_app._jobs["fake-job"] = {"status": "running"}
        res = self.client.get("/api/status/fake-job")
        data = json.loads(res.data)
        self.assertEqual(data["status"], "running")

    def test_jobs_list_endpoint(self):
        res = self.client.get("/api/jobs")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(json.loads(res.data), list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
