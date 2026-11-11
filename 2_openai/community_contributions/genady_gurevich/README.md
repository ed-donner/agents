# Lab 3 – Sandbox Agent in Docker

A variant of `2_openai/3_lab3.ipynb` where the optional **Sandbox Agents** example runs inside a Docker container (`DockerSandboxClient`, `python:3.14-slim`) instead of `UnixLocalSandboxClient`. This lets it run on plain Windows, without WSL, using Docker Desktop or Podman Desktop with Docker compatibility enabled.

Changes from the original:
- The agent reads code from `/workspace/code` and writes fixes to `/workspace/output` inside the container. The fixed files are then copied back to `./output` on the host.
- The notebook creates the sandbox session itself, so the files are still there after `Runner.run` returns. The `finally` block deletes the container.
- Workaround: `session.supports_pty = lambda: False`, because the Docker PTY exec path drops non-tty command output.

## Requirements

- A running Docker-compatible engine (`docker.from_env().ping()` should return `True`)
- The Docker extra for the Agents SDK: `uv add "openai-agents[docker]"`
