FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 7860

# Environment variables
ENV PYTHONPATH=/app
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV GRADIO_PORT=7861

# Run the application
CMD ["python", "main.py"]
