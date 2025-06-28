"""Sleep.me Entity class."""

from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME
from .coordinator import SleepmeDataUpdateCoordinator
from .data import SleepmeConfigEntry


class SleepmeEntity(CoordinatorEntity):
    """Sleep.me Entity base class."""

    def __init__(
        self,
        coordinator: SleepmeDataUpdateCoordinator,
        config_entry: SleepmeConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        data = self.coordinator.data[self.config_entry.entry_id]
        about_data = data.get("about")
        control_data = data.get("control")
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": NAME,
            "model": about_data.get("model"),
            "manufacturer": NAME,
            "serial_number": about_data.get("serial_number"),
            "mac_address": about_data.get("mac_address"),
            "lan_address": about_data.get("lan_address"),
            "ip_address": about_data.get("ip_address"),
            "firmware_version": about_data.get("firmware_version"),
            "time_zone": control_data.get("time_zone"),
        }

    @property
    def device_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        data = self.coordinator.data[self.config_entry.entry_id]
        status_data = data.get("status")
        return {
            "attribution": ATTRIBUTION,
            "id": self.config_entry.entry_id,
            "integration": DOMAIN,
            "brightness_level": status_data.get("brightness_level"),
        }

    async def async_turn_on(self) -> None:
        """
        Turn the device on.

        This method should be implemented by subclasses.
        """
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """
        Turn the device off.

        This method should be implemented by subclasses.
        """
        await self.coordinator.async_request_refresh()
