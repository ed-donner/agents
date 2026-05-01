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
