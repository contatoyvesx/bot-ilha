# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy application code
COPY bot.json ./bot.py

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir fastapi "uvicorn[standard]" openai requests

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "8000"]
