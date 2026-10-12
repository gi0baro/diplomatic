from .. import cache


@cache.redis(duration=300)
def cached_user_stats(user):
    return user.stats()
