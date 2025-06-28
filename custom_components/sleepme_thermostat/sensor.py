"""Sleep.me Sensor integration for Home Assistant."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import LOGGER, SENSOR_TYPES
from .coordinator import SleepmeDataUpdateCoordinator
from .data import SleepmeConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: SleepmeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sleep.me sensors from a config entry."""
    coordinator = config_entry.runtime_data.coordinator

    entities = []
    for sensor_type in SENSOR_TYPES:
        for idx in coordinator.data:
            entities.append(SleepmeSensor(coordinator, idx, sensor_type))
            LOGGER.debug(f"Adding sensor {sensor_type} for device {idx}")

    async_add_entities(entities)


class SleepmeSensor(CoordinatorEntity, SensorEntity):
    """Sleep.me Sensor Entity."""

    def __init__(
        self,
        coordinator: SleepmeDataUpdateCoordinator,
        idx: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.idx = idx
        self._sensor_type = sensor_type

        data = coordinator.data[idx]

        self._name = f"{data['name']} {SENSOR_TYPES[sensor_type]}"
        self._unique_id = f"{idx}_{sensor_type}"

        LOGGER.info(
            f"Initializing SleepmeSensor with device info: "
            f"{coordinator.data[idx]}, and sensor type: {sensor_type}"
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
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        try:
            status = self.coordinator.data[self.idx].get("status", {})
            LOGGER.debug(f"Status for device {self.idx}: {status}")
            return status.get(self._sensor_type)
        except KeyError:
            LOGGER.error(
                f"Error fetching state for sensor {self._unique_id}: "
                f"{self.coordinator.data[self.idx]}"
            )
            return None

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self._sensor_type == "water_temperature_f":
            return UnitOfTemperature.FAHRENHEIT
        if self._sensor_type == "water_temperature_c":
            return UnitOfTemperature.CELSIUS
        if self._sensor_type == "water_level":
            return PERCENTAGE
        return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class."""
        if self._sensor_type in ["water_temperature_f", "water_temperature_c"]:
            return SensorDeviceClass.TEMPERATURE
        return None
