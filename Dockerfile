FROM python:3.11-slim

# Säker och stabil Python setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies för PostgreSQL och andra verktyg
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installera Python dependencies först (caching!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera applikationen
COPY main.py .

# Exponera port
EXPOSE 8000

# Starta FastAPI med Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]