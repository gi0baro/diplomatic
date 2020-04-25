FROM cr.amira.io/nudiplomacy/web/base:latest

EXPOSE 8000

ENTRYPOINT [ "emmett", "-a", "nudiplomacy" ]
CMD [ "serve", "--no-access-log", "--max-queue", "512" ]
