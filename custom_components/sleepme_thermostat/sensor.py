from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import LOGGER
from .const import SENSOR_TYPES
from .coordinator import SleepmeDataUpdateCoordinator
from .data import SleepmeConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SleepmeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = config_entry.runtime_data.coordinator

    async_add_entities(
        [
            SleepmeSensor(coordinator, idx, sensor_type)
            for idx, ent in coordinator.data.items()
            for sensor_type in SENSOR_TYPES
        ]
    )


class SleepmeSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: SleepmeDataUpdateCoordinator,
        idx: str,
        sensor_type: str,
    ):
        super().__init__(coordinator)
        self.idx = idx
        self._sensor_type = sensor_type
        self._name = f"{coordinator.data[idx]['name']} {SENSOR_TYPES[sensor_type]}"
        self._unique_id = f"{idx}_{sensor_type}"
        self._state = None

        LOGGER.info(
            f"Initializing SleepmeSensor with device info: {coordinator.data[idx]}, and sensor type: {sensor_type}"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = (
            self.coordinator.data[self.idx]
            .get("control", {})
            .get("thermal_control_status")
            == "active"
        )
        self.async_write_ha_state()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        try:
            status = self.coordinator.data[self.idx].get("status", {})
            LOGGER.debug(f"Status for sensor {self._unique_id}: {status}")
            if self._sensor_type == "water_temperature_f":
                return status.get("water_temperature_f")
            elif self._sensor_type == "water_temperature_c":
                return status.get("water_temperature_c")
            elif self._sensor_type == "water_level":
                return status.get("water_level")
        except KeyError:
            LOGGER.error(
                f"Error fetching state for sensor {self._unique_id}: {self.coordinator.data[self.idx]}"
            )
            return None

    @property
    def unit_of_measurement(self):
        if self._sensor_type == "water_temperature_f":
            return UnitOfTemperature.FAHRENHEIT
        elif self._sensor_type == "water_temperature_c":
            return UnitOfTemperature.CELSIUS
        elif self._sensor_type == "water_level":
            return PERCENTAGE

    @property
    def device_class(self):
        if self._sensor_type in ["water_temperature_f", "water_temperature_c"]:
            return SensorDeviceClass.TEMPERATURE
