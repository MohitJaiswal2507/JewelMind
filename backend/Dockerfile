# ==============================================================================
# JewelMind Backend API Dockerfile
# Multi-stage production container for FastAPI backend
# ==============================================================================

FROM python:3.10-slim AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a wheel/virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Final Production Stage
# ==============================================================================
FROM python:3.10-slim AS runner

WORKDIR /app

# Install minimal runtime libraries (libpq for postgres/supabase connection, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Create a non-privileged user for security
RUN groupadd -g 10001 jewelmind && \
    useradd -u 10000 -g jewelmind -s /bin/bash -m jewelmind_app && \
    chown -R jewelmind_app:jewelmind /app

# Copy application source code
COPY --chown=jewelmind_app:jewelmind . /app

USER jewelmind_app

EXPOSE 8000

# Health check using FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production startup command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
