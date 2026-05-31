from __future__ import annotations

from pathlib import Path

import modal

APP_NAME = "week1-project-agent"
SECRET_NAME = "week1-project-secrets"

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "week1_project"
REQUIREMENTS_FILE = PROJECT_DIR / "requirements.txt"

# Build a Modal image with your dependencies and project code.
image = (
	modal.Image.debian_slim(python_version="3.11")
	.pip_install_from_requirements(str(REQUIREMENTS_FILE))
	.env({"PYTHONPATH": "/app/week1_project"})
	.add_local_dir(str(PROJECT_DIR), remote_path="/app/week1_project")
)

app = modal.App(APP_NAME)


@app.function(
	image=image,
	secrets=[modal.Secret.from_name(SECRET_NAME)],
	# Keep a single warm container for sticky chat sessions.
	min_containers=1,
	max_containers=1,
	timeout=600,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def gradio_app():
	# Import inside the image context so Modal bundles and resolves dependencies correctly.
	with image.imports():
		import gradio as gr
		from fastapi import FastAPI

		from agent_core import build_gradio_app

	demo = build_gradio_app()
	fastapi_app = FastAPI()

	# Mount Gradio into a FastAPI ASGI app for Modal serving.
	return gr.mount_gradio_app(fastapi_app, demo, path="/")
