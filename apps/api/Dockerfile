# DermaCare Agent — API Production Dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements if present, or install core packages
RUN pip install --no-cache-dir \
    pillow \
    pyyaml \
    pyjwt \
    cryptography \
    bcrypt

# Copy application source
COPY . /app

ENV PYTHONPATH="/app/apps/api:/app"
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "apps/api/app/main.py"]
