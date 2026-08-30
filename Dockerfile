# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Install dependencies
# (Bind mounts are used to avoid copying the files into the layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# ---------------------------------------------------
# Runtime Stage
FROM python:3.12-slim-bookworm

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . /app

# Ensure we use the virtualenv Python
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
