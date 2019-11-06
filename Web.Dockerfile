FROM python:3.7-alpine

MAINTAINER gi0baro

RUN apk add --no-cache libpq nodejs

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app
COPY requirements.web.txt /usr/src/app
RUN apk add --no-cache --virtual build-deps \
    g++ musl-dev postgresql-dev && \
    pip install -r /usr/src/app/requirements.txt && \
    pip install -r /usr/src/app/requirements.web.txt && \
    apk del build-deps

WORKDIR /app
COPY diplomacy diplomacy
COPY nudiplomacy nudiplomacy
COPY variants variants

EXPOSE 8000

CMD [ "gunicorn", "weppyweb:app", "--bind=0.0.0.0:8000", "--threads=2", "--worker-tmp-dir=/dev/shm", "--log-file=-" ]
