import threading
import time


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=15):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.probe_sent = False
        self.lock = threading.Lock()

    def _update_state(self):
        with self.lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.probe_sent = False

    def call(self, func, *args, **kwargs):
        self._update_state()

        with self.lock:
            if self.state == "OPEN":
                raise CircuitBreakerOpenException(
                    "Circuit is OPEN. Fast failing request."
                )
            if self.state == "HALF_OPEN":
                if self.probe_sent:
                    raise CircuitBreakerOpenException(
                        "Circuit is HALF_OPEN and probe is already in flight."
                    )
                self.probe_sent = True

        try:
            result = func(*args, **kwargs)
            # Success - reset breaker
            with self.lock:
                self.failure_count = 0
                self.state = "CLOSED"
                self.probe_sent = False
            return result
        except Exception as e:
            # If it's a specific Gemini 503 or 429, we should count it
            # For this prototype, we'll count all exceptions
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                self.probe_sent = False

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"

            raise e

    async def async_call(self, func, *args, **kwargs):
        self._update_state()

        with self.lock:
            if self.state == "OPEN":
                raise CircuitBreakerOpenException(
                    "Circuit is OPEN. Fast failing request."
                )
            if self.state == "HALF_OPEN":
                if self.probe_sent:
                    raise CircuitBreakerOpenException(
                        "Circuit is HALF_OPEN and probe is already in flight."
                    )
                self.probe_sent = True

        try:
            result = await func(*args, **kwargs)
            # Success - reset breaker
            with self.lock:
                self.failure_count = 0
                self.state = "CLOSED"
                self.probe_sent = False
            return result
        except Exception as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                self.probe_sent = False

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"

            raise e
