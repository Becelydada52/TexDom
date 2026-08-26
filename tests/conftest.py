from __future__ import annotations

import pytest

from app.web.ratelimit import feedback_rate_limiter


@pytest.fixture(autouse=True)
def _reset_feedback_rate_limiter():
    feedback_rate_limiter.reset()
    yield
    feedback_rate_limiter.reset()
