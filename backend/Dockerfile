FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (layer caching — only re-installs if these change)
COPY pyproject.toml uv.lock ./

# Install dependencies into /app/.venv
RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the installed venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/

# Use venv python
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Shell form so $PORT (injected by Render) expands; falls back to 8000 locally.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
