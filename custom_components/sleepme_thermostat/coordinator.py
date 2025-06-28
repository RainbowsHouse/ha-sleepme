"""DataUpdateCoordinator for Sleep.me."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SleepmeApiClientAuthenticationError, SleepmeApiClientError
from .const import LOGGER

if TYPE_CHECKING:
    from .data import SleepmeConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class SleepmeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: SleepmeConfigEntry
    _devices: list[dict]

    async def async_set_device_mode(self, device_id: str, mode: str) -> None:
        """Set the device mode."""
        control = await self.config_entry.runtime_data.client.async_set_device_mode(
            device_id, mode
        )
        self.data[device_id]["control"] = control

    async def _async_setup(self) -> None:
        """
        Set up the coordinator.

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
                    device_id = device["id"]
                    data = await api.async_get_device_state(device_id)
                    results[device_id] = data
                    LOGGER.info(
                        f"Device {device['name']} state: "
                        f"{json.dumps(results[device_id], indent=2)}"
                    )
        except SleepmeApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except SleepmeApiClientError as exception:
            LOGGER.error(f"Error fetching data: {exception}")
            raise
        else:
            return results
