"""DataUpdateCoordinator for Sleep.me."""

from __future__ import annotations

import json
from typing import Any

import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import SleepmeApiClientAuthenticationError
from .api import SleepmeApiClientError
from .const import LOGGER
from .data import SleepmeConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class SleepmeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: SleepmeConfigEntry
    _devices: list[dict]

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        self._devices = await self.config_entry.runtime_data.client.async_get_devices()

        LOGGER.info(f"Devices: {[device['name'] for device in self._devices]}")

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            api = self.config_entry.runtime_data.client
            results = {}
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                for device in self._devices:
                    id = device["id"]
                    data = await api.async_get_device_state(id)

                    results[id] = {**device, **data}

                    LOGGER.info(
                        f"Device {device['name']} state: {json.dumps(results[id], indent=2)}"
                    )
            return results
        except SleepmeApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except SleepmeApiClientError as exception:
            raise UpdateFailed(exception) from exception
