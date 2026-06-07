# ── Stage 1: build / install dependencies ──────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools and pip-tools
RUN pip install --no-cache-dir hatchling

COPY pyproject.toml .
# Install runtime deps only (no dev extras)
RUN pip install --no-cache-dir "fastapi>=0.111.0" "uvicorn[standard]>=0.29.0" "pydantic>=2.7.0"

# ── Stage 2: runtime image ─────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy application source
COPY main.py .

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
