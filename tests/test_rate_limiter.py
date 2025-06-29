"""Tests for the RateLimiter module."""

import threading
import time
from unittest.mock import patch

import pytest

from custom_components.sleepme_thermostat.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for the RateLimiter class."""

    def test_initialization_default(self) -> None:
        """Test RateLimiter initialization with default parameters."""
        limiter = RateLimiter()
        assert limiter.max_requests == 10
        assert limiter.request_count == 0
        assert isinstance(limiter.lock, threading.Lock)

    def test_initialization_custom_limit(self) -> None:
        """Test RateLimiter initialization with custom limit."""
        limiter = RateLimiter(max_requests_per_minute=5)
        assert limiter.max_requests == 5
        assert limiter.request_count == 0

    def test_can_send_request_initial_state(self) -> None:
        """Test can_send_request returns True when no requests have been made."""
        limiter = RateLimiter(max_requests_per_minute=3)
        assert limiter.can_send_request() is True

    def test_can_send_request_below_limit(self) -> None:
        """Test can_send_request returns True when below the limit."""
        limiter = RateLimiter(max_requests_per_minute=3)
        limiter.record_request()
        limiter.record_request()
        assert limiter.can_send_request() is True

    def test_can_send_request_at_limit(self) -> None:
        """Test can_send_request returns False when at the limit."""
        limiter = RateLimiter(max_requests_per_minute=2)
        limiter.record_request()
        limiter.record_request()
        assert limiter.can_send_request() is False

    def test_can_send_request_above_limit(self) -> None:
        """Test can_send_request returns False when above the limit."""
        limiter = RateLimiter(max_requests_per_minute=1)
        limiter.record_request()
        limiter.record_request()  # This shouldn't normally happen, but test it
        assert limiter.can_send_request() is False

    def test_record_request_increments_count(self) -> None:
        """Test record_request increments the request count."""
        limiter = RateLimiter(max_requests_per_minute=5)
        assert limiter.request_count == 0
        limiter.record_request()
        assert limiter.request_count == 1
        limiter.record_request()
        assert limiter.request_count == 2

    def test_check_limits_resets_on_new_minute(self) -> None:
        """Test check_limits resets count when minute changes."""
        with patch("time.time") as mock_time:
            # Start at minute 100
            mock_time.return_value = 6000  # 100 minutes * 60 seconds
            limiter = RateLimiter(max_requests_per_minute=3)
            limiter.record_request()
            limiter.record_request()
            assert limiter.request_count == 2

            # Move to minute 101
            mock_time.return_value = 6060  # 101 minutes * 60 seconds
            limiter.check_limits()
            assert limiter.request_count == 0
            assert limiter.current_minute == 101

    def test_check_limits_no_reset_same_minute(self) -> None:
        """Test check_limits doesn't reset count in same minute."""
        with patch("time.time") as mock_time:
            mock_time.return_value = 6000  # 100 minutes * 60 seconds
            limiter = RateLimiter(max_requests_per_minute=3)
            limiter.record_request()
            assert limiter.request_count == 1

            # Still in same minute
            mock_time.return_value = 6030  # 100.5 minutes * 60 seconds
            limiter.check_limits()
            assert limiter.request_count == 1
            assert limiter.current_minute == 100

    def test_can_send_request_resets_on_new_minute(self) -> None:
        """Test can_send_request resets when minute changes."""
        with patch("time.time") as mock_time:
            # Start at minute 100
            mock_time.return_value = 6000  # 100 minutes * 60 seconds
            limiter = RateLimiter(max_requests_per_minute=2)
            limiter.record_request()
            limiter.record_request()
            assert limiter.can_send_request() is False

            # Move to minute 101
            mock_time.return_value = 6060  # 101 minutes * 60 seconds
            assert limiter.can_send_request() is True

    def test_record_request_resets_on_new_minute(self) -> None:
        """Test record_request resets when minute changes."""
        with patch("time.time") as mock_time:
            # Start at minute 100
            mock_time.return_value = 6000  # 100 minutes * 60 seconds
            limiter = RateLimiter(max_requests_per_minute=2)
            limiter.record_request()
            limiter.record_request()
            assert limiter.request_count == 2

            # Move to minute 101
            mock_time.return_value = 6060  # 101 minutes * 60 seconds
            limiter.record_request()
            assert limiter.request_count == 1

    @pytest.mark.asyncio
    async def test_wait_for_reset_no_wait_when_below_limit(self) -> None:
        """Test wait_for_reset doesn't wait when below limit."""
        limiter = RateLimiter(max_requests_per_minute=3)
        limiter.record_request()

        start_time = time.time()
        await limiter.wait_for_reset()
        end_time = time.time()

        # Should not wait significantly
        assert end_time - start_time < 0.1

    @pytest.mark.asyncio
    async def test_wait_for_reset_waits_when_at_limit(self) -> None:
        """Test wait_for_reset waits when at limit."""
        with patch("time.time") as mock_time:
            # Start at minute 100, 30 seconds in
            mock_time.return_value = 6030  # 100 minutes * 60 seconds + 30 seconds
            limiter = RateLimiter(max_requests_per_minute=1)
            limiter.record_request()

            # Should wait until next minute (30 seconds)
            with patch("asyncio.sleep") as mock_sleep:
                await limiter.wait_for_reset()
                mock_sleep.assert_called_once_with(30.0)

    @pytest.mark.asyncio
    async def test_wait_for_reset_waits_when_above_limit(self) -> None:
        """Test wait_for_reset waits when above limit."""
        with patch("time.time") as mock_time:
            # Start at minute 100, 45 seconds in
            mock_time.return_value = 6045  # 100 minutes * 60 seconds + 45 seconds
            limiter = RateLimiter(max_requests_per_minute=1)
            limiter.record_request()
            limiter.record_request()  # Above limit

            # Should wait until next minute (15 seconds)
            with patch("asyncio.sleep") as mock_sleep:
                await limiter.wait_for_reset()
                mock_sleep.assert_called_once_with(15.0)

    @pytest.mark.asyncio
    async def test_wait_for_reset_no_wait_at_minute_boundary(self) -> None:
        """Test wait_for_reset doesn't wait at minute boundary."""
        with patch("time.time") as mock_time:
            # Start at minute 100, 59.9 seconds in
            mock_time.return_value = 6059.9  # 100 minutes * 60 seconds + 59.9 seconds
            limiter = RateLimiter(max_requests_per_minute=1)
            limiter.record_request()

            # Should wait very little time
            with patch("asyncio.sleep") as mock_sleep:
                await limiter.wait_for_reset()
                # Use assert_called_once() and check the argument separately to handle floating point precision
                assert mock_sleep.call_count == 1
                actual_wait_time = mock_sleep.call_args[0][0]
                assert (
                    abs(actual_wait_time - 0.1) < 0.001
                )  # Allow for small floating point differences

    def test_thread_safety_multiple_threads(self) -> None:
        """Test thread safety with multiple threads."""
        limiter = RateLimiter(max_requests_per_minute=100)
        results = []

        def worker():
            """Worker function for thread safety test."""
            for _ in range(10):
                if limiter.can_send_request():
                    limiter.record_request()
                    results.append(True)
                else:
                    results.append(False)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify total requests don't exceed limit
        assert limiter.request_count <= 100
        # Verify we got some successful requests
        assert any(results)

    def test_edge_case_zero_requests_per_minute(self) -> None:
        """Test edge case with zero requests per minute."""
        limiter = RateLimiter(max_requests_per_minute=0)
        assert limiter.can_send_request() is False
        limiter.record_request()
        assert limiter.can_send_request() is False

    def test_edge_case_negative_requests_per_minute(self) -> None:
        """Test edge case with negative requests per minute."""
        limiter = RateLimiter(max_requests_per_minute=-1)
        assert limiter.can_send_request() is False
        limiter.record_request()
        assert limiter.can_send_request() is False

    def test_edge_case_very_large_requests_per_minute(self) -> None:
        """Test edge case with very large requests per minute."""
        limiter = RateLimiter(max_requests_per_minute=1000000)
        # Should be able to make many requests
        for _ in range(1000):
            assert limiter.can_send_request() is True
            limiter.record_request()
        assert limiter.request_count == 1000

    def test_concurrent_access_pattern(self) -> None:
        """Test realistic concurrent access pattern."""
        limiter = RateLimiter(max_requests_per_minute=5)

        def concurrent_worker():
            """Worker that checks and records requests concurrently."""
            for _ in range(3):
                if limiter.can_send_request():
                    limiter.record_request()
                    time.sleep(0.001)  # Small delay to increase concurrency

        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=concurrent_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should not exceed the limit
        assert limiter.request_count <= 5
