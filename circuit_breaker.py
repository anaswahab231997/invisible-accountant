import time

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=15):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED" # CLOSED, OPEN, HALF_OPEN

    def _update_state(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                
    def call(self, func, *args, **kwargs):
        self._update_state()
        
        if self.state == "OPEN":
            raise CircuitBreakerOpenException("Circuit is OPEN. Fast failing request.")
            
        try:
            result = func(*args, **kwargs)
            # Success - reset breaker
            self.failure_count = 0
            self.state = "CLOSED"
            return result
        except Exception as e:
            # If it's a specific Gemini 503 or 429, we should count it
            # For this prototype, we'll count all exceptions
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                
            raise e
