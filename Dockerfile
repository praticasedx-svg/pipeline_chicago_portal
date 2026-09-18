FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOCAL_RAW_FILE_PATH=/tmp/payments.parquet

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src ./src
COPY main.py ./

CMD ["sh", "-c", "/app/.venv/bin/functions-framework --target ingest_payments --host 0.0.0.0 --port ${PORT:-8080}"]
