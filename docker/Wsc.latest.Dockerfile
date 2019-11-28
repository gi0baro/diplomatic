FROM cr.amira.io/nudiplomacy/web/base:latest

MAINTAINER gi0baro

ENTRYPOINT [ "celery", "-A", "nudiplomacy:celery" ]
CMD [ "beat", "--loglevel=INFO" ]
