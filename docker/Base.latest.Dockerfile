FROM cr.amira.io/nudiplomacy/web/py:latest

MAINTAINER gi0baro

WORKDIR /app
COPY diplomacy diplomacy
COPY nudiplomacy nudiplomacy
COPY variants variants
