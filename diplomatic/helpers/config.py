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
