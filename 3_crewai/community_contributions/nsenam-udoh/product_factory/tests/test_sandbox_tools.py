import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from product_factory.tools.sandbox_reset import reset_workstream
from product_factory.tools.sandbox_tools import (
    MAX_READ_CHARS,
    MAX_WRITE_CHARS,
    RUN_TIMEOUT_SECONDS,
    WRITE_PREVIEW_CHARS,
    make_sandbox_tools,
)


class SandboxToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "workstream"
        self.tools = {
            item.name: item for item in make_sandbox_tools(self.root)
        }

    def tearDown(self):
        self.temporary.cleanup()

    def test_paths_cannot_escape_sandbox(self):
        outside = Path(self.temporary.name) / "outside.txt"
        outside.write_text("keep", encoding="utf-8")
        for name, kwargs in [
            ("read_sandbox_file", {"filename": "../outside.txt"}),
            ("write_sandbox_file", {"filename": "../outside.txt", "content": "no"}),
            ("delete_sandbox_file", {"filename": "../outside.txt"}),
            ("run_sandbox_python", {"filename": "../outside.py"}),
        ]:
            with self.subTest(name=name):
                self.assertIn("Path escapes sandbox", self.tools[name].run(**kwargs))
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")

    def test_delete_removes_files_but_refuses_directories(self):
        (self.root / "probe.txt").write_text("temporary", encoding="utf-8")
        (self.root / "folder").mkdir()
        deleted = self.tools["delete_sandbox_file"].run(filename="probe.txt")
        refused = self.tools["delete_sandbox_file"].run(filename="folder")
        self.assertIn("Deleted sandbox file: probe.txt", deleted)
        self.assertFalse((self.root / "probe.txt").exists())
        self.assertIn("Refusing to delete a non-file", refused)
        self.assertTrue((self.root / "folder").is_dir())

    def test_list_prunes_environments_and_caches(self):
        (self.root / ".venv" / "lib64").mkdir(parents=True)
        (self.root / ".venv" / "lib64" / "hidden.py").write_text(
            "hidden", encoding="utf-8"
        )
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "cached.pyc").write_bytes(b"cached")
        (self.root / "backend.py").write_text("visible", encoding="utf-8")
        result = self.tools["list_sandbox_files"].run()
        self.assertEqual(result, "backend.py")

    def test_list_returns_walk_errors(self):
        with patch(
            "product_factory.tools.sandbox_tools.os.walk",
            side_effect=OSError("listing failed"),
        ):
            result = self.tools["list_sandbox_files"].run()
        self.assertEqual(result, "listing failed")

    def test_utf8_roundtrip_and_nested_file(self):
        content = "Hello, 世界\n café\n"
        result = self.tools["write_sandbox_file"].run(
            filename="nested/greeting.txt", content=content
        )
        self.assertIn("Wrote", result)
        self.assertEqual(
            self.tools["read_sandbox_file"].run(filename="nested/greeting.txt"),
            content,
        )

    def test_write_returns_hash_and_capped_preview(self):
        content = "x" * (WRITE_PREVIEW_CHARS + 100)
        result = self.tools["write_sandbox_file"].run(
            filename="nested/large.txt", content=content
        )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self.assertIn(
            f"Wrote {WRITE_PREVIEW_CHARS + 100} characters to nested/large.txt",
            result,
        )
        self.assertIn(f"SHA256: {digest}", result)
        self.assertIn(
            f"Preview (first {WRITE_PREVIEW_CHARS} characters):", result
        )
        self.assertTrue(result.endswith(content[:WRITE_PREVIEW_CHARS]))

    def test_read_truncates_to_cap(self):
        path = self.root / "large.txt"
        path.write_text("x" * (MAX_READ_CHARS + 500), encoding="utf-8")
        result = self.tools["read_sandbox_file"].run(filename="large.txt")
        self.assertLessEqual(len(result), MAX_READ_CHARS)
        self.assertIn("[Truncated:", result)

    def test_read_supports_line_range(self):
        path = self.root / "ranged.py"
        path.write_text("a\nb\nc\nd\n", encoding="utf-8")
        result = self.tools["read_sandbox_file"].run(
            filename="ranged.py", start_line=2, end_line=3
        )
        self.assertIn("Lines 2-3 of 4:", result)
        self.assertIn("b\nc\n", result)
        self.assertNotIn("a\n", result)
        self.assertNotIn("d\n", result)

    def test_read_empty_and_out_of_range(self):
        (self.root / "empty.txt").write_text("", encoding="utf-8")
        self.assertEqual(
            self.tools["read_sandbox_file"].run(filename="empty.txt"),
            "",
        )
        out_of_range = self.tools["read_sandbox_file"].run(
            filename="empty.txt", start_line=2
        )
        self.assertIn("No lines in range 2-end (0 lines total).", out_of_range)
        self.assertNotIn("Lines 2-0", out_of_range)

    def test_write_cap_rejects_oversized_content(self):
        result = self.tools["write_sandbox_file"].run(
            filename="large.py", content="x" * (MAX_WRITE_CHARS + 1)
        )
        self.assertIn("Write rejected", result)
        self.assertFalse((self.root / "large.py").exists())

    def test_every_tool_disables_caching(self):
        for item in self.tools.values():
            with self.subTest(tool=item.name):
                self.assertFalse(item.cache_function("args", "result"))

    def test_python_run_uses_resource_limits_and_labels_output(self):
        (self.root / "check.py").write_text("print('ok')", encoding="utf-8")
        completed = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")
        with patch(
            "product_factory.tools.sandbox_tools.subprocess.run",
            return_value=completed,
        ) as run:
            result = self.tools["run_sandbox_python"].run(filename="check.py")
        command = run.call_args.args[0]
        self.assertEqual(command[:2], ["docker", "run"])
        self.assertIn("--memory", command)
        self.assertIn("--cpus", command)
        self.assertIn("--pids-limit", command)
        self.assertIn("GRADIO_ANALYTICS_ENABLED=False", command)
        self.assertEqual(run.call_args.kwargs["timeout"], RUN_TIMEOUT_SECONDS)
        self.assertTrue(result.startswith("Ran: uv run check.py\n"))
        self.assertIn("Exit code: 0", result)
        self.assertIn("--- stdout ---\nok", result)
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
        self.assertEqual(run.call_args.kwargs["errors"], "replace")

    def test_timeout_force_removes_named_container(self):
        (self.root / "slow.py").write_text("pass", encoding="utf-8")
        timeout = subprocess.TimeoutExpired(
            "docker", RUN_TIMEOUT_SECONDS, output="partial"
        )
        with patch(
            "product_factory.tools.sandbox_tools.subprocess.run",
            side_effect=[timeout, SimpleNamespace(returncode=0)],
        ) as run:
            result = self.tools["run_sandbox_python"].run(filename="slow.py")
        self.assertTrue(result.startswith("Ran: uv run slow.py\n"))
        self.assertIn(
            f"timed out after {RUN_TIMEOUT_SECONDS} seconds", result
        )
        self.assertIn("Do NOT start a Gradio/web server", result)
        self.assertIn("GRADIO_ANALYTICS_ENABLED=False", run.call_args_list[0].args[0])
        cleanup = run.call_args_list[1].args[0]
        self.assertEqual(cleanup[:3], ["docker", "rm", "-f"])
        self.assertTrue(cleanup[3].startswith("pf-"))

    def test_app_check_stops_when_container_exits(self):
        (self.root / "app.py").write_text("raise TypeError('bad launch')")
        responses = [
            SimpleNamespace(returncode=0, stdout="container-id\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="false\n", stderr=""),
            SimpleNamespace(
                returncode=0,
                stdout="Traceback\nTypeError: bad launch\n",
                stderr="",
            ),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        ]
        with patch(
            "product_factory.tools.sandbox_tools.subprocess.run",
            side_effect=responses,
        ) as run, patch(
            "product_factory.tools.sandbox_tools.urlopen"
        ) as http, patch(
            "product_factory.tools.sandbox_tools.time.sleep"
        ) as sleep:
            result = self.tools["check_sandbox_app"].run()

        self.assertIn("FAILED", result)
        self.assertIn("App exited before serving HTTP 200.", result)
        self.assertIn("TypeError: bad launch", result)
        http.assert_not_called()
        sleep.assert_not_called()
        inspect = run.call_args_list[1].args[0]
        self.assertEqual(
            inspect[:4], ["docker", "inspect", "-f", "{{.State.Running}}"]
        )
        cleanup = run.call_args_list[-1].args[0]
        self.assertEqual(cleanup[:3], ["docker", "rm", "-f"])
        self.assertEqual(cleanup[3], inspect[4])


class ResetTests(unittest.TestCase):
    def test_reset_recreates_only_the_requested_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "sandbox" / "main"
            other = base / "sandbox" / "other"
            root.mkdir(parents=True)
            other.mkdir(parents=True)
            (root / "old.py").write_text("old", encoding="utf-8")
            (other / "keep.py").write_text("keep", encoding="utf-8")
            with patch(
                "product_factory.tools.sandbox_reset.subprocess.run"
            ) as run:
                reset_workstream(root)
            self.assertTrue(root.is_dir())
            self.assertFalse((root / "old.py").exists())
            self.assertEqual((other / "keep.py").read_text(encoding="utf-8"), "keep")
            self.assertEqual(
                [call.args[0] for call in run.call_args_list],
                [
                    ["uv", "init", "--bare", "--no-workspace", "--python", "3.13"],
                    ["uv", "add", "gradio"],
                ],
            )
            for call in run.call_args_list:
                self.assertEqual(call.kwargs["cwd"], root)
                self.assertTrue(call.kwargs["check"])


if __name__ == "__main__":
    unittest.main()
