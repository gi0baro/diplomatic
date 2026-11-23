import os

from celery.schedules import crontab, solar


def parse_celery_cron(data):
    for task_data in data.values():
        if "crontab" in task_data:
            kwargs = task_data["crontab"]
            del task_data["crontab"]
            task_data["schedule"] = crontab(**kwargs)
        if "solar" in task_data:
            kwargs = task_data["solar"]
            del task_data["solar"]
            task_data["schedule"] = solar(kwargs["event"], kwargs["lat"], kwargs["lon"])
    return data


def load_config(app):
    app.config_from_yaml("app.yml")

    app.config.build_commit = os.environ.get("APP_COMMIT", "master")
    app.config.url_default_namespace = "main"
    app.config.internal_hostname = os.environ.get("INTERNAL_HOSTNAME", "localhost")
    app.config.internal_port = os.environ.get("INTERNAL_PORT", "8000")
    app.config.internal_fqdn = f"{app.config.internal_hostname}:{app.config.internal_port}"
    app.config.site_url = os.environ.get("SITE_URL", app.config.site_url)
    app.config.uploads_folder = os.path.join(app.root_path, app.config.uploads_folder)

    app.config.auth.registration_verification = os.environ.get("AUTH_EMAIL_VERIFICATION", "1") == "1"
    app.config.auth.hmac_key = os.environ.get("AUTH_HMAC_KEY")
    app.config.sessions_key = os.environ.get("SESSIONS_KEY", "diplomatic")

    #: the mailer is loaded only when a server is given
    app.config.mailer.server = os.environ.get("MAILER_SERVER")
    app.config.mailer.port = int(os.environ.get("MAILER_PORT", 25))
    app.config.mailer.username = os.environ.get("MAILER_USERNAME")
    app.config.mailer.password = os.environ.get("MAILER_PASSWORD")
    app.config.mailer.use_tls = os.environ.get("MAILER_TLS", "0") == "1"
    app.config.mailer.use_ssl = os.environ.get("MAILER_SSL", "0") == "1"
    app.config.mailer.sender = os.environ.get("MAILER_SENDER", "noreply@diplomatic.live")

    #: the extension does nothing without a DSN
    app.config.Sentry.dsn = os.environ.get("SENTRY_DSN")
    app.config.Sentry.environment = os.environ.get("SENTRY_ENVIRONMENT", "production")
    app.config.Sentry.release = app.config.build_commit

    app.config.db.host = os.environ.get("POSTGRES_HOST", "localhost")
    app.config.db.user = os.environ.get("POSTGRES_USER", app.name)
    app.config.db.password = os.environ.get("POSTGRES_PASSWORD", app.name)
    app.config.db.database = os.environ.get("POSTGRES_DB", app.name)
    app.config.db.pool_size = int(os.environ.get("POSTGRES_POOL_SIZE", 4))

    app.config.redis.host = os.environ.get("REDIS_HOST", "localhost")
    app.config.redis.port = int(os.environ.get("REDIS_PORT", 6379))

    app.config.worker.broker = os.environ.get("WRK_BROKER_URL", "redis://localhost:6379/1")

    app.config.Haml.set_as_default = True
