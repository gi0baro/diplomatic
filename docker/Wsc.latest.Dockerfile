FROM cr.amira.io/nudiplomacy/web/base:latest

ENTRYPOINT [ "celery", "-A", "nudiplomacy:celery" ]
CMD [ "beat", "--loglevel=INFO" ]
