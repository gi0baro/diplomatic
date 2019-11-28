FROM cr.amira.io/nudiplomacy/web/base:latest

MAINTAINER gi0baro

EXPOSE 8000

ENTRYPOINT [ "emmett", "-a", "nudiplomacy" ]
CMD [ "serve", "--access-log", "false", "--max-queue", "512" ]
