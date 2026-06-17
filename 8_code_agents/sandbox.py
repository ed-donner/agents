"""
Sandboxed Python executor.
Runs untrusted code in a subprocess with a hard timeout and no network access.
Returns stdout, stderr, exit code, and elapsed time.
"""

import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    elapsed_seconds: float
    timed_out: bool

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def summary(self) -> str:
        status = "PASS" if self.success else ("TIMEOUT" if self.timed_out else "FAIL")
        lines = [f"[{status}] exit={self.exit_code} time={self.elapsed_seconds:.2f}s"]
        if self.stdout.strip():
            lines.append("--- stdout ---")
            lines.append(self.stdout[:2000])
        if self.stderr.strip():
            lines.append("--- stderr ---")
            lines.append(self.stderr[:2000])
        return "\n".join(lines)


def run_code(code: str, timeout: float = 10.0) -> RunResult:
    """Execute Python code string in an isolated subprocess."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(textwrap.dedent(code))
        tmp_path = f.name

    start = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start
        return RunResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            elapsed_seconds=elapsed,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            stdout="",
            stderr=f"Timed out after {timeout}s",
            exit_code=-1,
            elapsed_seconds=timeout,
            timed_out=True,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def run_pytest(test_code: str, source_code: str, timeout: float = 30.0) -> RunResult:
    """
    Write source + test to a temp directory, run pytest, return results.
    source_code   → solution.py
    test_code     → test_solution.py
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / "solution.py"
        test_path = Path(tmpdir) / "test_solution.py"
        src_path.write_text(textwrap.dedent(source_code))
        # Prepend the import so test file can use `from solution import ...`
        full_test = "from solution import *\n\n" + textwrap.dedent(test_code)
        test_path.write_text(full_test)

        start = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            elapsed = time.monotonic() - start
            return RunResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                elapsed_seconds=elapsed,
                timed_out=False,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                stdout="",
                stderr=f"pytest timed out after {timeout}s",
                exit_code=-1,
                elapsed_seconds=timeout,
                timed_out=True,
            )


if __name__ == "__main__":
    # Quick smoke test
    result = run_code("print('hello from sandbox')")
    print(result.summary())

    bad = run_code("x = 1/0")
    print(bad.summary())
