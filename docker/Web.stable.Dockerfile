FROM cr.amira.io/nudiplomacy/web/base:stable

MAINTAINER gi0baro

EXPOSE 8000

ENTRYPOINT [ "emmett", "-a", "nudiplomacy" ]
CMD [ "serve", "--access-log", "false", "--max-queue", "512" ]
