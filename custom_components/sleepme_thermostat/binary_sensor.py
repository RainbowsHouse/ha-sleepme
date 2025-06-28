"""Sleep.me Binary Sensor integration for Home Assistant."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BINARY_SENSOR_TYPES, LOGGER
from .coordinator import SleepmeDataUpdateCoordinator
from .data import SleepmeConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: SleepmeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sleep.me binary sensors from a config entry."""
    coordinator = config_entry.runtime_data.coordinator

    entities = []
    for sensor_type in BINARY_SENSOR_TYPES:
        for idx in coordinator.data:
            entities.append(SleepmeBinarySensor(coordinator, idx, sensor_type))
            LOGGER.debug(f"Adding binary sensor {sensor_type} for device {idx}")

    async_add_entities(entities)


class SleepmeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Sleep.me Binary Sensor Entity."""

    def __init__(
        self,
        coordinator: SleepmeDataUpdateCoordinator,
        idx: str,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.idx = idx
        self._sensor_type = sensor_type

        data = coordinator.data[idx]

        self._name = f"{data['name']} {BINARY_SENSOR_TYPES[sensor_type]}"
        self._unique_id = f"{idx}_{sensor_type}"

        LOGGER.debug(
            f"Initializing SleepmeBinarySensor with device info: "
            f"{coordinator.data[idx]}, and sensor type: {sensor_type}"
        )

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the binary sensor."""
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        try:
            status = self.coordinator.data[self.idx].get("status", {})
            LOGGER.debug(f"Status for device {self.idx}: {status}")
            return status.get("is_connected", False)
        except KeyError:
            LOGGER.error(
                f"Error fetching state for binary sensor {self._unique_id}: "
                f"{self.coordinator.data[self.idx]}"
            )
            return None
