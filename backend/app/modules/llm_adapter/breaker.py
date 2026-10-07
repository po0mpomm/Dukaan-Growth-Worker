"""
Circuit Breaker for external LLM calls (TRD §2.1)
After 3 consecutive failures, trips open for 10 minutes and forces template fallback.
"""

import time
import structlog

log = structlog.get_logger(__name__)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_seconds: int = 600):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_seconds
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            log.warning("circuit_breaker_opened", failure_count=self.failure_count)

    def can_attempt(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
                log.info("circuit_breaker_half_open")
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return True
