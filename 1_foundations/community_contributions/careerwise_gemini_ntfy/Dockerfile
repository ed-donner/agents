# Use official Python image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port
EXPOSE 8080

# Command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "backend_api:app", "--host", "0.0.0.0", "--port", "8080"]
