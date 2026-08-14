FROM python:3.12-slim

WORKDIR /app

COPY src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./

WORKDIR /
COPY info/ ./info/

# Render sets $PORT dynamically — Gradio must bind to it
ENV GRADIO_SERVER_NAME=0.0.0.0
EXPOSE 7860

WORKDIR /app

CMD ["python", "main.py"]