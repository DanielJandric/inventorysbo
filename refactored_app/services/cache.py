from __future__ import annotations

import time
from typing import Any, Optional


class InMemoryCache:
    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        it = self._store.get(key)
        if not it:
            return None
        ts, val = it
        if ts < time.time():
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        self._store[key] = (time.time() + ttl, value)

    def invalidate(self, prefix: str | None = None) -> None:
        if not prefix:
            self._store.clear()
            return
        for k in list(self._store.keys()):
            if k.startswith(prefix):
                self._store.pop(k, None)


cache = InMemoryCache()

