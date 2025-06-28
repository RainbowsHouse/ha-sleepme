"""Sample API Client."""

from __future__ import annotations

import logging
import socket
from dataclasses import dataclass
from typing import cast

import aiohttp
import async_timeout

from .const import LOGGER
from .rate_limiter import RateLimiter

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class SleepmeApiClientError(Exception):
    """Exception to indicate a general API error."""


class SleepmeApiClientCommunicationError(
    SleepmeApiClientError,
):
    """Exception to indicate a communication error."""


class SleepmeApiClientAuthenticationError(
    SleepmeApiClientError,
):
    """Exception to indicate an authentication error."""


class SleepmeApiClientRateLimitError(
    SleepmeApiClientError,
):
    """Exception to indicate a rate limit error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise SleepmeApiClientAuthenticationError(
            msg,
        )
    if response.status == 429:
        msg = "Rate limit exceeded"
        raise SleepmeApiClientRateLimitError(
            msg,
        )
    response.raise_for_status()


@dataclass
class SleepmeDevice:
    """Data for a Sleep.me device."""

    id: str
    name: str


@dataclass
class SleepmeDeviceState:
    """Data for a Sleep.me device state."""

    about: dict
    control: dict
    status: dict


class SleepmeApiClient:
    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Sleep.me API Client."""
        self._api_key = api_key
        self._session = session
        self._rate_limiter = rate_limiter or RateLimiter()

    async def async_get_data(self) -> list[dict]:
        """Get data from the API."""
        return await self.async_get_devices()

    async def async_get_devices(self) -> list[dict]:
        """Get devices from the API."""
        url = "https://api.developer.sleep.me/v1/devices"
        devices = cast(list[dict], await self.api_wrapper("get", url))

        return [
            device
            for device in devices
            if "CHILIPAD_PRO" in device.get("attachments", [])
        ]

    async def async_get_device_state(self, device_id: str) -> dict:
        """Get device state from the API."""
        url = f"https://api.developer.sleep.me/v1/devices/{device_id}"
        return await self.api_wrapper("get", url)

    async def async_set_device_temperature(
        self, device_id: str, temperature: float
    ) -> dict:
        """Set device temperature from the API."""
        url = f"https://api.developer.sleep.me/v1/devices/{device_id}"
        return await self.api_wrapper(
            "patch", url, data={"set_temperature_f": temperature}
        )

    async def async_set_device_mode(self, device_id: str, mode: str) -> dict:
        """Set device mode from the API."""
        url = f"https://api.developer.sleep.me/v1/devices/{device_id}"
        return await self.api_wrapper(
            "patch", url, data={"thermal_control_status": mode}
        )

    async def api_wrapper(self, method: str, url: str, data: dict = {}) -> dict:
        """Get information from the API."""
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {self._api_key}"

        if not self._rate_limiter.can_send_request():
            # wait for rate limit to reset
            # await self._rate_limiter.wait_for_reset()
            LOGGER.info("Rate limit exceeded")

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise SleepmeApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise SleepmeApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise SleepmeApiClientError(
                msg,
            ) from exception
