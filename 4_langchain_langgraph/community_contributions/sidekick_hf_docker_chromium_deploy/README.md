# How to deploy Sidekick to HuggingFace using Docker

### Why does Sidekick need Docker deployment:

Playwright is built off Chromium and requires Chromium installation regardless headless or not. HuggingFace Gradio deployment will get

```
Executable doesn’t exist at /root/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome
```

This error means Playwright’s **Python code is present**, but the **Chromium binary Playwright expects is not present at runtime**.

### HugginFace Deployment Gradio vs. Docker:

There are a couple of facts regarding to HuggingFace deployment. Each application deployment requires a new space. Spaces can be roughly categorized by SDK installed: Gradio or Docker. Each space comes with a HuggingFace github space repo . `uv run gradio deploy` will create a space with Gradio SDK installed and upload all files to that repo.  It also will honor versioned defined in `uv.lock`. The README.md of my Gradio deployment will have the followings

```
title: sidekick
app_file: app.py
sdk: gradio
sdk_version: 5.49.1
```

`5.49.1` is the gradio version defined in uv.lock. You are on your own if you deploy your app using Docker - clone that repo, commit and push all files, including Dockerfile, modified README.md and pin versions of python modules in requirement.txt if needed

### Why is Sidekick docker deployment so complicated?

You might notice that it is trying to access `root` folder which is not accessible from user.  There would be a mis-match unless we let Playwright know where to install Chromium. Gradio deployment will take care of Gradio app-port: 7860 and where to bind Gradio and EXPOSE port. We have to take care of those ourselves in Docker deployment.

```
Executable doesn’t exist at /root/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome
```

The followings are the excerpt of a working README.md

```
sdk: docker
app_port: 7860
```

and a working copy of DockerFile

```
FROM python:3.12-slim

# Put Playwright browsers in a deterministic path, not ~/.cache.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install beautifulsoup4
RUN pip install lxml
RUN pip install wikipedia
# Install browser + Linux deps. Use --only-shell if you only need headless.
RUN python -m playwright install --with-deps --only-shell chromium

# Hugging Face Docker Spaces run as uid 1000. Create and switch to that user.
RUN useradd -m -u 1000 user
RUN chown -R 1000:1000 /app /ms-playwright
USER user

COPY --chown=user:user . /app

# Gradio needs to be reachable from outside the container.
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

EXPOSE 7860
CMD ["python", "app.py"]
```

### Summary

* Use a **Docker Space**. Set `sdk: docker` and `app_port: 7860`.
* Install Playwright browsers at build time, and avoid HOME-dependent cache paths by setting `PLAYWRIGHT_BROWSERS_PATH`.
* Respect HF’s **UID 1000** runtime and permissions.
* Bind Gradio to `0.0.0.0:7860`.
* Use Gradio queue and low concurrency for Playwright tasks.
* Need to pin specific version of Gradio etcs since Gradio 6 is not compatible with 5.

**Special thanks for a HuggingFace forum user `john6666` to come up with key points of Dockerfile and README.md**

### Github Codes:

https://github.com/threecuptea/agents

### The demo:

https://huggingface.co/spaces/threecuptea/sidekick-docker
