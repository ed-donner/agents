import subprocess
from agents import function_tool

g_docker_resp = ''

# For fallback case, due to issues with open source llm
def get_docker_resp():
    return g_docker_resp


@function_tool
def run_docker() -> str:  # type: ignore[override]
    """Run docker tool to get today's date"""

    # Tunables
    image: str = "pyrepl-sandbox:latest"
    timeout_s: int = 60
    mem: str = "256m"
    cpus: str = "1"
    pids: int = 128
    output_limit: int = 1000  # truncate overly long output

    code = 'from datetime import date; print(date.today())'
    import sys
    print('Code to run in docker:', code, file=sys.stderr)

    cmd = [
        "docker", "run", "--rm",
        "--network", "none", "--read-only",
        "--cpus", cpus, "--memory", mem,
        "--pids-limit", str(pids),
        "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        image, "bash", "-lc", f"python - <<'PYEOF'\n{code}\nPYEOF"
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return "Execution timed out."

    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    print('Docker returned:', out, file=sys.stderr)
    global g_docker_resp
    g_docker_resp = out

    if len(out) > output_limit:
        out = out[:output_limit] + "\n... [truncated]"
    if proc.returncode != 0 and not out:
        return f"Process exited with code {proc.returncode} and no output."
    return out.strip() or "(no output)"

