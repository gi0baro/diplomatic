FROM cr.amira.io/nudiplomacy/web/base:stable

EXPOSE 8000

ENTRYPOINT [ "emmett", "-a", "nudiplomacy" ]
CMD [ "serve", "--no-access-log", "--max-queue", "512" ]
