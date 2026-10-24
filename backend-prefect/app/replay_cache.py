"""Caché anti-replay en memoria: (user_id, código) -> instante en que expira el bloqueo."""

import threading
import time

from . import config


class AntiReplayCache:
    def __init__(self, ttl_seconds: int = config.ANTI_REPLAY_SECONDS) -> None:
        self.ttl = ttl_seconds
        self._used: dict[tuple[str, str], float] = {}
        self._lock = threading.Lock()

    def _purge(self, now: float) -> None:
        for key in [k for k, exp in self._used.items() if exp <= now]:
            del self._used[key]

    def was_used(self, user_id: str, code: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            return (user_id, code) in self._used

    def mark_used(self, user_id: str, code: str) -> None:
        with self._lock:
            self._used[(user_id, code)] = time.monotonic() + self.ttl


replay_cache = AntiReplayCache()
