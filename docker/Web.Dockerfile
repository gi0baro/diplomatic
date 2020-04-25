ARG SRC_IMAGE

FROM ${SRC_IMAGE}

EXPOSE 8000

ENTRYPOINT [ "emmett", "-a", "nudiplomacy" ]
CMD [ "serve", "--no-access-log", "--max-queue", "512" ]
