FROM node:12-alpine AS front

WORKDIR /front

COPY front/game-board/package.json front/game-board/package-lock.json ./
RUN npm ci

COPY front/game-board .
RUN npm run tailwind && \
    npm run build -- --target wc --inline-vue --name game-board src/Build.vue && \
    npm run postcss


FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gcc git libc6-dev && \
    curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH=/root/.cargo/bin:$PATH

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY diplomatico diplomatico
RUN uv sync --frozen --no-dev --no-editable --no-install-project


FROM python:3.13-slim-bookworm AS base

# nodejs: emmett-assets compiles .coffee sources at request time through PyExecJS
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv .venv
ENV PATH=/app/.venv/bin:$PATH

COPY diplomatic diplomatic
COPY variants variants
COPY --from=front /front/dist/game-board.min.js diplomatic/static/gboard/game-board.js
COPY --from=front /front/dist/tw.min.css diplomatic/static/gboard/tw.css


FROM base AS web

EXPOSE 8000

ENTRYPOINT ["emmett", "-a", "diplomatic"]
CMD ["serve", "--no-access-log"]


FROM base AS worker

ENV C_FORCE_ROOT=yup

ENTRYPOINT ["celery", "-A", "diplomatic:celery"]
CMD ["worker", "-Q", "games", "--loglevel=INFO", "--concurrency=1"]


FROM base AS scheduler

ENV C_FORCE_ROOT=yup

ENTRYPOINT ["celery", "-A", "diplomatic:celery"]
CMD ["beat", "--loglevel=INFO"]
