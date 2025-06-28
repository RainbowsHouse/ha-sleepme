import asyncio
import threading
import time
from typing import Optional


class RateLimiter:
    """
    Tracks and enforces a maximum number of requests per discrete minute.
    Thread-safe for use in concurrent environments.
    """

    def __init__(self, max_requests_per_minute: int = 10) -> None:
        self.max_requests = max_requests_per_minute
        self.lock = threading.Lock()
        self.current_minute: Optional[int] = None
        self.request_count = 0

    def can_send_request(self) -> bool:
        """
        Returns True if a request can be sent in the current minute, False otherwise.
        """
        with self.lock:
            self.check_limits()
            return self.request_count < self.max_requests

    def record_request(self) -> None:
        """
        Records a request. Should be called after confirming can_send_request() is True.
        """
        with self.lock:
            self.check_limits()
            self.request_count += 1

    async def wait_for_reset(self) -> None:
        """
        Waits for the rate limit to reset.
        """
        with self.lock:
            self.check_limits()
            await asyncio.sleep(60 - (time.time() % 60))

    def check_limits(self) -> None:
        """
        Checks and resets the rate limit if necessary.
        """
        now_minute = int(time.time() // 60)
        if self.current_minute != now_minute:
            self.current_minute = now_minute
            self.request_count = 0
