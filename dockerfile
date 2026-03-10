# Base image
FROM python:3.11-slim

# Environment variables for secure and stable Python execution
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set exact working directory
WORKDIR /app

# Install merged system dependencies: 
# gcc and libpq-dev for PostgreSQL
# build-essential and librdkafka-dev for confluent-kafka
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager for deterministic dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency definitions
COPY pyproject.toml uv.lock* ./

# Install Python dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Copy the entire application (main.py, extract.py, transform.py, etc.)
COPY . .

# Expose API port
EXPOSE 8000

# Start FastAPI with Uvicorn via uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]