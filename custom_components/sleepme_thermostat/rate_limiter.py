"""Sleep.me Rate Limiter module."""

import asyncio
import threading
import time


class RateLimiter:
    """
    Tracks and enforces a maximum number of requests per discrete minute.

    Thread-safe for use in concurrent environments.
    """

    def __init__(self, max_requests_per_minute: int = 10) -> None:
        """Initialize the rate limiter."""
        self.max_requests = max_requests_per_minute
        self.lock = threading.Lock()
        self.current_minute = int(time.time() // 60)
        self.request_count = 0

    def can_send_request(self) -> bool:
        """Return True only if a request can be sent in the current minute."""
        with self.lock:
            self.check_limits()
            return self.request_count < self.max_requests

    def record_request(self) -> None:
        """
        Record a request.

        Should be called after confirming can_send_request() is True.
        """
        with self.lock:
            self.check_limits()
            self.request_count += 1

    async def wait_for_reset(self) -> None:
        """Wait for the rate limit to reset."""
        with self.lock:
            self.check_limits()
            if self.request_count >= self.max_requests:
                # Wait until the next minute
                current_time = time.time()
                next_minute = (int(current_time // 60) + 1) * 60
                wait_time = next_minute - current_time
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

    def check_limits(self) -> None:
        """Check and reset the rate limit if necessary."""
        now_minute = int(time.time() // 60)
        if self.current_minute != now_minute:
            self.current_minute = now_minute
            self.request_count = 0
