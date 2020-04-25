FROM python:3.7-alpine

RUN apk add --no-cache curl libpq libstdc++ nodejs

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
ENV PATH /root/.poetry/bin:$PATH
RUN poetry config virtualenvs.in-project true

RUN mkdir -p /usr/src/deps
COPY pyproject.toml /usr/src/deps
COPY poetry.lock /usr/src/deps

WORKDIR /usr/src/app

RUN apk add --no-cache --virtual build-deps \
    g++ git libffi-dev libuv-dev musl-dev make openssl-dev postgresql-dev && \
    poetry install && \
    apk del build-deps
ENV PATH /usr/src/deps/.venv/bin:$PATH
