"""Sleep.me Climate integration for Home Assistant."""

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SleepmeApiClient
from .const import LOGGER
from .coordinator import SleepmeDataUpdateCoordinator
from .data import SleepmeConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: SleepmeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sleep.me climate devices from a config entry."""
    coordinator = config_entry.runtime_data.coordinator

    devices = coordinator.data
    LOGGER.debug(f"Climate Devices: {devices}")

    async_add_entities(
        [SleepmeClimate(coordinator, idx) for idx, ent in coordinator.data.items()]
    )


class SleepmeClimate(CoordinatorEntity, ClimateEntity):
    """Sleep.me Climate Entity."""

    coordinator: SleepmeDataUpdateCoordinator
    _api: SleepmeApiClient

    def __init__(self, coordinator: SleepmeDataUpdateCoordinator, idx: str) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)

        self._api = coordinator.config_entry.runtime_data.client

        data = coordinator.data[idx]

        self.idx = idx
        self._name = data["name"]
        self._unique_id = f"{idx}_climate"

        self._state = data.get("control", {}).get("thermal_control_status") == "active"
        self._target_temperature = data.get("control", {}).get("set_temperature_f")
        self._current_temperature = data.get("status", {}).get("water_temperature_f")

        LOGGER.debug(
            f"Initializing SleepmeClimate with device info: {coordinator.data[idx]}"
        )

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available HVAC modes."""
        return [HVACMode.OFF, HVACMode.HEAT_COOL]

    @property
    def min_temp(self) -> int:
        """Return the minimum temperature."""
        return 55

    @property
    def max_temp(self) -> int:
        """Return the maximum temperature."""
        return 115

    @property
    def name(self) -> str:
        """Return the name of the climate entity."""
        return self._name

    @property
    def temperature_unit(self) -> UnitOfTemperature:
        """Return the unit of measurement."""
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        try:
            status = self.coordinator.data[self.idx].get("status", {})
            LOGGER.debug(f"Status for device {self.idx}: {status}")
            self._current_temperature = status.get("water_temperature_f")
            return status.get("water_temperature_f")
        except KeyError:
            LOGGER.error(
                f"Error fetching current temperature for device {self.idx}: "
                f"{self.coordinator.data[self.idx]}"
            )
            return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            temperature = int(temperature)
            LOGGER.debug(f"Setting target temperature to {temperature}F")
            self._target_temperature = temperature
            self.async_write_ha_state()  # Update the state immediately

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        try:
            control = self.coordinator.data[self.idx].get("control", {})
            LOGGER.debug(f"Control for device {self.idx}: {control}")
            return (
                HVACMode.HEAT_COOL
                if control.get("thermal_control_status") == "active"
                else HVACMode.OFF
            )
        except KeyError:
            LOGGER.error(
                f"Error fetching HVAC mode for device {self.idx}: "
                f"{self.coordinator.data[self.idx]}"
            )
            return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        mode = "active" if hvac_mode == HVACMode.HEAT_COOL else "standby"
        LOGGER.debug(f"Setting HVAC mode to {mode}")
        await self.coordinator.async_set_device_mode(self.idx, mode)

        if mode == "active":
            self._state = HVACMode.HEAT_COOL
        else:
            self._state = HVACMode.OFF

        self.async_write_ha_state()  # Update the state immediately

    async def async_update(self) -> None:
        """Update the climate entity."""
        await self.coordinator.async_request_refresh()
        device_state = self.coordinator.data[self.idx]
        self._state = (
            device_state.get("control", {}).get("thermal_control_status") == "active"
        )
        self._target_temperature = device_state.get("control", {}).get(
            "set_temperature_f"
        )
        self._current_temperature = device_state.get("status", {}).get(
            "water_temperature_f"
        )
