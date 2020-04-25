FROM cr.amira.io/nudiplomacy/web/base:stable

ENTRYPOINT [ "celery", "-A", "nudiplomacy:celery" ]
CMD [ "beat", "--loglevel=INFO" ]
