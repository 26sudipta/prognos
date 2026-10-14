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

# Copy application code + migration files (alembic runs at startup)
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Use venv python
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Apply DB migrations (retried), then start the server. See
# docker-entrypoint.sh: migrations are no longer chained with `&&`, so a
# transient Neon connect at boot cannot leave the service with no instance.
COPY docker-entrypoint.sh ./
# Invoked via `sh` so the image does not depend on the executable bit
# surviving the COPY — a "permission denied" here would reproduce the exact
# no-healthy-instance state this script exists to prevent.
CMD ["sh", "./docker-entrypoint.sh"]
