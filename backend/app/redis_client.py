from redis import Redis

from app.config import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def close_redis() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
