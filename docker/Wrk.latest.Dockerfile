FROM cr.amira.io/nudiplomacy/web/base:latest

MAINTAINER gi0baro

ENTRYPOINT [ "celery", "-A", "nudiplomacy:celery" ]
CMD [ "worker", "-Q", "games", "--loglevel=INFO", "--concurrency=1" ]
