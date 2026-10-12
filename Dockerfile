FROM denoland/deno:2.9.7 AS css

COPY css /wrk/css
COPY diplomatic/templates /wrk/diplomatic/templates
WORKDIR /wrk/css

ENV NODE_ENV=production

RUN deno run -A tailwindcss -i src/tailwind.css -c tailwind.config.js -o dist/main.css --minify


FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gcc git libc6-dev && \
    curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH=/root/.cargo/bin:$PATH

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY diplomatico diplomatico
RUN uv sync --frozen --no-dev --no-editable --no-install-project


FROM python:3.14-slim-bookworm AS base

# nodejs: emmett-assets compiles .coffee sources at request time through PyExecJS
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv .venv
ENV PATH=/app/.venv/bin:$PATH

COPY diplomatic diplomatic
COPY variants variants
COPY --from=css /wrk/css/dist/main.css diplomatic/static/bundled/main.css


FROM base AS web

EXPOSE 8000

ENTRYPOINT ["emmett", "-a", "diplomatic.web"]
CMD ["serve", "--no-access-log"]


FROM base AS worker

ENV C_FORCE_ROOT=yup

ENTRYPOINT ["celery", "-A", "diplomatic:celery"]
CMD ["worker", "-Q", "games", "--loglevel=INFO", "--concurrency=1"]


FROM base AS scheduler

ENV C_FORCE_ROOT=yup

ENTRYPOINT ["celery", "-A", "diplomatic:celery"]
CMD ["beat", "--loglevel=INFO"]
