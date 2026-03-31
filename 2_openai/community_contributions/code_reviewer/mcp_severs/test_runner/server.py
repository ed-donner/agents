import asyncio
import json
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("test-runner")

TIMEOUT = int(os.environ.get("TEST_RUNNER_TIMEOUT", "120"))


def _detect_framework(repo_dir):
    root = Path(repo_dir)
    if (root / "pytest.ini").exists() or (root / "setup.cfg").exists():
        return "pytest"
    if list(root.rglob("test_*.py")) or list(root.rglob("*_test.py")):
        return "pytest"
    if (root / "package.json").exists():
        try:
            pkg = json.loads((root / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            scripts = pkg.get("scripts", {})
            if "jest" in deps or "jest" in scripts.get("test", ""):
                return "jest"
            if "mocha" in deps:
                return "mocha"
        except Exception:
            pass
    if (root / "go.mod").exists():
        return "go test"
    return ""


def _parse_test_output(framework, stdout, stderr):
    summary = {"framework": framework}
    combined = stdout + stderr
    for line in combined.splitlines():
        line_lower = line.lower()
        if any(k in line_lower for k in ["passed", "failed", "error", "tests:", "passing", "failing"]):
            summary["result_line"] = line.strip()
            break
    return summary


def _parse_coverage(repo_dir, framework):
    root = Path(repo_dir)

    if framework == "pytest":
        coverage_file = root / "coverage.json"
        if coverage_file.exists():
            try:
                data = json.loads(coverage_file.read_text())
                totals = data.get("totals", {})
                return {
                    "total_coverage_percent": totals.get("percent_covered_display", "N/A"),
                    "covered_lines": totals.get("covered_lines", 0),
                    "total_lines": totals.get("num_statements", 0),
                    "missing_lines": totals.get("missing_lines", 0)
                }
            except Exception:
                pass

    elif framework == "jest":
        summary_file = root / "coverage" / "coverage-summary.json"
        if summary_file.exists():
            try:
                data = json.loads(summary_file.read_text())
                total = data.get("total", {})
                return {
                    "lines_percent": total.get("lines", {}).get("pct", "N/A"),
                    "functions_percent": total.get("functions", {}).get("pct", "N/A"),
                    "branches_percent": total.get("branches", {}).get("pct", "N/A"),
                    "statements_percent": total.get("statements", {}).get("pct", "N/A")
                }
            except Exception:
                pass

    return {"note": "Coverage file not found. Ensure pytest-cov or jest --coverage ran successfully."}


@mcp.tool()
async def run_tests(repo_dir, test_framework = "auto"):
    """Run the test suite of a repository and return a pass/fail summary."""
    if not Path(repo_dir).is_dir():
        return {"success": False, "error": f"Directory not found: '{repo_dir}'"}

    framework = (
        _detect_framework(repo_dir)
        if test_framework == "auto"
        else test_framework
    )

    if not framework:
        return {
            "success": False,
            "error": "Could not detect a test framework. Ensure test files are present."
        }

    commands = {
        "pytest":   ["pytest", "--tb=short", "-q"],
        "unittest": ["python", "-m", "unittest", "discover", "-v"],
        "jest":     ["npx", "jest", "--no-coverage"],
        "mocha":    ["npx", "mocha", "--reporter", "min"],
        "go test":  ["go", "test", "./..."]
    }

    cmd = commands.get(framework)
    if not cmd:
        return {"success": False, "error": f"Unsupported framework: '{framework}'"}

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        return {
            "success": True,
            "framework": framework,
            "passed": proc.returncode == 0,
            "return_code": proc.returncode,
            "summary": _parse_test_output(framework, stdout_text, stderr_text),
            "stdout": stdout_text[-3000:],
            "stderr": stderr_text[-1000:]
        }

    except asyncio.TimeoutError:
        return {"success": False, "error": f"Test run timed out after {TIMEOUT} seconds."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_coverage_report(repo_dir, test_framework = "pytest"):
    """Run tests with coverage and return a per-file coverage summary."""
    if not Path(repo_dir).is_dir():
        return {"success": False, "error": f"Directory not found: '{repo_dir}'"}

    commands = {
        "pytest": ["pytest", "--cov=.", "--cov-report=json", "-q"],
        "jest": ["npx", "jest", "--coverage", "--coverageReporters=json-summary", "--silent"]
    }

    cmd = commands.get(test_framework)
    if not cmd:
        return {"success": False, "error": f"Coverage not supported for: '{test_framework}'"}

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        stdout_text = stdout.decode("utf-8", errors="replace")

        return {
            "success": True,
            "framework": test_framework,
            "coverage": _parse_coverage(repo_dir, test_framework),
            "stdout": stdout_text[-3000:]
        }

    except asyncio.TimeoutError:
        return {"success": False, "error": f"Coverage run timed out after {TIMEOUT} seconds."}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()