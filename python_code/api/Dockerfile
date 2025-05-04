# Use Python image with explicit platform for cloud compatibility
FROM --platform=linux/amd64 python:3.8-slim

# Set environment variables to ensure Python doesn't create .pyc files and runs in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Add performance optimizations for Python
ENV PYTHONOPTIMIZE=2

# Add debugging environment variables
ENV LOG_LEVEL=INFO
ENV DEBUG_ORDER_PROCESSING=true

# Install system dependencies for performance
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements first to leverage Docker cache
COPY requirements.txt requirements.txt

# Install dependencies with optimizations
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary files
COPY recommendation_objects/ recommendation_objects/
COPY agents/ agents/
COPY agent_controller.py agent_controller.py
COPY main.py main.py

# Testing Dockerfile
COPY test_input.json test_input.json

# Make sure the entry point is executable
RUN chmod +x main.py

# Add healthcheck to monitor the application
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Use explicit path to python interpreter with optimizations
CMD ["python3", "-O", "main.py"]