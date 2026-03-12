FROM python:3.11-slim

# Miljövariabler
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Arbetar i /app katalogen
WORKDIR /app

# Installera nödvändiga paket
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Installera uv
RUN pip install uv

# Kopiera projektfiler
COPY pyproject.toml uv.lock ./

# Installera beroenden
RUN uv sync --frozen

# Kopiera övriga filer
COPY . .

# Exponera port 8000
EXPOSE 8000

# Starta applikationen
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]