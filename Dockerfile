FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml .
RUN pip install --no-cache-dir "fastapi>=0.111.0" "uvicorn[standard]>=0.29.0" "pydantic>=2.7.0"

FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY main.py .

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]