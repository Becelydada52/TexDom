from __future__ import annotations

import time
from collections import deque


class RateLimiter:
    def __init__(self, max_events: int = 5, window_seconds: float = 900.0) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        events = self._events.setdefault(key, deque())

        while events and now - events[0] >= self.window_seconds:
            events.popleft()

        if len(events) >= self.max_events:
            return False

        events.append(now)
        return True

    def reset(self) -> None:
        self._events.clear()


feedback_rate_limiter = RateLimiter(max_events=5, window_seconds=15 * 60)
