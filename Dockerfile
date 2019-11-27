FROM python:3.7-alpine

MAINTAINER gi0baro

RUN apk add --no-cache libpq nodejs

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app
RUN apk add --no-cache --virtual build-deps \
    g++ musl-dev make git libffi-dev libuv-dev postgresql-dev && \
    pip install -r /usr/src/app/requirements.txt && \
    apk del build-deps

WORKDIR /app
COPY diplomacy diplomacy
COPY nudiplomacy nudiplomacy
COPY variants variants
