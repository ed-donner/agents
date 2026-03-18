# Hugging Face Spaces requires port 7860 and a non-root user (uid 1000)
FROM python:3.11-slim

WORKDIR /app

# System deps needed by pypdf and general build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HF Spaces executes containers as uid 1000
RUN useradd -m -u 1000 user
USER user

EXPOSE 7860

CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]
