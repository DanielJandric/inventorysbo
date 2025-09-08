import os
import json
import time
import ssl
import redis


_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_ssl_required = _redis_url.startswith("rediss://") or os.getenv("REDIS_USE_SSL", "0") == "1"
_redis = redis.from_url(
    _redis_url,
    ssl_cert_reqs=ssl.CERT_NONE if _ssl_required else None,
)


def cache_get(key: str):
    value = _redis.get(key)
    return json.loads(value) if value else None


def cache_set(key: str, payload, ttl: int = 60) -> None:
    _redis.setex(key, ttl, json.dumps(payload))


