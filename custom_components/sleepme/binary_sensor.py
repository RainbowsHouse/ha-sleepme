from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BINARY_SENSOR_TYPES
from .const import LOGGER
from .data import SleepmeConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SleepmeConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator = config_entry.runtime_data.coordinator
    entities = []

    for sensor_type in BINARY_SENSOR_TYPES:
        for idx, ent in coordinator.data.items():
            entities.append(SleepmeBinarySensor(coordinator, idx, sensor_type))
            LOGGER.debug(f"Adding binary sensor {sensor_type} for device {idx}")

    async_add_entities(entities)


class SleepmeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, idx, sensor_type):
        super().__init__(coordinator)
        self.idx = idx
        self._sensor_type = sensor_type
        self._name = (
            f"{coordinator.data[idx]['name']} {BINARY_SENSOR_TYPES[sensor_type]}"
        )
        self._unique_id = f"{idx}_{sensor_type}"
        self._state = None

        LOGGER.debug(
            f"Initializing SleepmeBinarySensor with device info: {coordinator.data[idx]}, and sensor type: {sensor_type}"
        )

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def is_on(self):
        try:
            status = self.coordinator.data[self.idx].get("status", {})
            LOGGER.debug(f"Status for binary sensor {self._unique_id}: {status}")
            if self._sensor_type == "is_water_low":
                return status.get("is_water_low")
            elif self._sensor_type == "is_connected":
                return status.get("is_connected")
        except KeyError:
            LOGGER.error(
                f"Error fetching state for binary sensor {self._unique_id}: {self.coordinator.data[self.idx]}"
            )
            return None
