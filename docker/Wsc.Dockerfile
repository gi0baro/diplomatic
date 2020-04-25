ARG SRC_IMAGE

FROM ${SRC_IMAGE}

ENTRYPOINT [ "celery", "-A", "nudiplomacy:celery" ]
CMD [ "beat", "--loglevel=INFO" ]
