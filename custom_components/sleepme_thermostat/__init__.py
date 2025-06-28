"""Sleep.me Thermostat integration for Home Assistant."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import SleepmeApiClient
from .const import CONF_UPDATE_INTERVAL, DOMAIN, LOGGER, STARTUP_MESSAGE
from .coordinator import SleepmeDataUpdateCoordinator
from .data import SleepmeData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SleepmeConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: SleepmeConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        LOGGER.info(STARTUP_MESSAGE)

    LOGGER.info(f"Setup entry for {entry.entry_id}")

    coordinator = SleepmeDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(minutes=entry.data[CONF_UPDATE_INTERVAL]),
    )

    entry.runtime_data = SleepmeData(
        client=SleepmeApiClient(
            api_key=entry.data[CONF_API_KEY],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # debug coordinator data
    LOGGER.info(f"Coordinator data: {json.dumps(coordinator.data, indent=2)}")

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SleepmeConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: SleepmeConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
