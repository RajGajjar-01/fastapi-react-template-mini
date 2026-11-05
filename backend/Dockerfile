FROM python:3.13-slim AS builder
# Pinned uv release; bump deliberately instead of tracking :latest.
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

FROM python:3.13-slim
WORKDIR /app
# Run as an unprivileged user.
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app app/ ./app
COPY --chown=app:app migrations/ ./migrations
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER app
EXPOSE 8000
# /live is cheap and needs no database; /openapi.json can be switched off with ENABLE_DOCS=false.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/live')"
# --proxy-headers makes request.client the real client address. Uvicorn only
# trusts the forwarded header from FORWARDED_ALLOW_IPS (default 127.0.0.1), so
# set that to your proxy's address when running behind one.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
