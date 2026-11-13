from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import app
from product_factory.flow import run_flow
from product_factory.main import run
from product_factory.tools.sandbox_reset import (
    reset_workstream,
    workstream_lock_path,
)


class WorkstreamLockTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "sandbox" / "main"
        self.lock = workstream_lock_path(self.root)
        self.root.mkdir(parents=True)

    def tearDown(self):
        self.temporary.cleanup()

    def flow_mock(self):
        flow = MagicMock()
        flow.kickoff.return_value = {"trace_link": "http://trace"}
        return flow

    def test_lock_removed_after_success(self):
        flow = self.flow_mock()

        def check_locked(**_kwargs):
            self.assertTrue(self.lock.is_file())
            return {"trace_link": "http://trace"}

        flow.kickoff.side_effect = check_locked
        with (
            patch("product_factory.flow.workstream_root", return_value=self.root),
            patch("product_factory.flow.ProductFactoryFlow", return_value=flow),
            patch("product_factory.flow._reset_workstream") as reset,
        ):
            result = run_flow(reset=True)
        self.assertEqual(result["trace_link"], "http://trace")
        reset.assert_called_once_with(self.root)
        self.assertFalse(self.lock.exists())

    def test_lock_removed_after_exception(self):
        flow = self.flow_mock()
        flow.kickoff.side_effect = RuntimeError("build failed")
        with (
            patch("product_factory.flow.workstream_root", return_value=self.root),
            patch("product_factory.flow.ProductFactoryFlow", return_value=flow),
        ):
            with self.assertRaisesRegex(RuntimeError, "build failed"):
                run_flow()
        self.assertFalse(self.lock.exists())

    def test_second_run_is_refused_while_locked(self):
        self.lock.write_text("locked", encoding="utf-8")
        with (
            patch("product_factory.flow.workstream_root", return_value=self.root),
            patch("product_factory.flow.ProductFactoryFlow") as factory,
        ):
            with self.assertRaises(RuntimeError) as caught:
                run_flow()
        self.assertIn(str(self.lock), str(caught.exception))
        self.assertIn("delete the lock file manually", str(caught.exception))
        factory.assert_not_called()

    def test_reset_is_refused_while_locked(self):
        kept = self.root / "wanted.py"
        kept.write_text("keep", encoding="utf-8")
        self.lock.write_text("locked", encoding="utf-8")
        with patch("product_factory.tools.sandbox_reset._rmtree") as remove:
            with self.assertRaises(RuntimeError) as caught:
                reset_workstream(self.root)
        self.assertIn(str(self.lock), str(caught.exception))
        remove.assert_not_called()
        self.assertEqual(kept.read_text(encoding="utf-8"), "keep")

    def test_feedback_skips_default_reset(self):
        with (
            patch("product_factory.main.run_flow", return_value={}) as run_flow_mock,
            patch("builtins.print"),
        ):
            run("main", "requirements", "continue this build", True)
        run_flow_mock.assert_called_once_with(
            "main", "requirements", "continue this build", False
        )

    def test_ui_shows_lock_errors_as_status(self):
        message = f"Workstream is locked by an active build: {self.lock}"
        app._set_job(running=False)
        with (
            patch("app.workstream_root", return_value=self.root),
            patch("app.reset_workstream", side_effect=RuntimeError(message)),
        ):
            status, _, _ = app._reset("main", True)
        self.assertIn(message, status)
        with patch("app.run_flow", side_effect=RuntimeError(message)):
            app._worker("main", "requirements", "")
        self.assertIn(message, app._snapshot()[0])


if __name__ == "__main__":
    unittest.main()
