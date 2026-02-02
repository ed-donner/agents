# IntellaPersona - Docker Deployment with Full Features
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements_docker.txt requirements.txt

# Install Python dependencies (Gradio 5.x with all features)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app_new.py .
COPY IntellectaLinkedIn.png .
COPY me/ ./me/

# Expose Gradio default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the application
CMD ["python", "app_new.py"]
