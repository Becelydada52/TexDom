from __future__ import annotations

import app.web.ratelimit as ratelimit_module
from app.web.ratelimit import RateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter(max_events=3, window_seconds=60)

    assert all(limiter.allow("ip") for _ in range(3))
    assert limiter.allow("ip") is False


def test_rate_limiter_keys_are_independent() -> None:
    limiter = RateLimiter(max_events=1, window_seconds=60)

    assert limiter.allow("client-a") is True
    assert limiter.allow("client-b") is True
    assert limiter.allow("client-a") is False


def test_rate_limiter_window_expiry(monkeypatch) -> None:
    limiter = RateLimiter(max_events=1, window_seconds=10)
    fake_now = [0.0]
    monkeypatch.setattr(ratelimit_module.time, "monotonic", lambda: fake_now[0])

    assert limiter.allow("ip") is True
    assert limiter.allow("ip") is False

    fake_now[0] += 11
    assert limiter.allow("ip") is True


def test_rate_limiter_reset() -> None:
    limiter = RateLimiter(max_events=1, window_seconds=60)

    assert limiter.allow("ip") is True
    limiter.reset()
    assert limiter.allow("ip") is True
