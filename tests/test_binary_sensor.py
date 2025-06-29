"""Tests for the SleepmeBinarySensor module."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.sleepme_thermostat.binary_sensor import (
    SleepmeBinarySensor,
    async_setup_entry,
)
from custom_components.sleepme_thermostat.const import BINARY_SENSOR_TYPES
from custom_components.sleepme_thermostat.coordinator import (
    SleepmeDataUpdateCoordinator,
)


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "dev1": {
            "name": "Bed 1",
            "status": {"is_connected": True},
        },
        "dev2": {
            "name": "Bed 2",
            "status": {"is_connected": False},
        },
    }
    return coordinator


@pytest.mark.asyncio
async def test_async_setup_entry_adds_entities(
    mock_coordinator: SleepmeDataUpdateCoordinator,
) -> None:
    """Test async_setup_entry adds all binary sensors for all devices and types."""
    mock_config_entry = MagicMock()
    mock_config_entry.runtime_data.coordinator = mock_coordinator
    added_entities = []

    def add_entities(new_entities, update_before_add=False):  # noqa: ANN001, ANN202, ARG001, FBT002
        """Mock add_entities function."""
        added_entities.extend(new_entities)

    hass = MagicMock()
    await async_setup_entry(hass, mock_config_entry, add_entities)

    # Should add one entity per device per sensor type
    expected_count = len(BINARY_SENSOR_TYPES) * len(mock_coordinator.data)
    assert len(added_entities) == expected_count
    # All should be SleepmeBinarySensor
    assert all(isinstance(e, SleepmeBinarySensor) for e in added_entities)


@pytest.mark.parametrize(
    ("sensor_type", "is_connected", "expected"),
    [
        ("is_connected", True, True),
        ("is_connected", False, False),
    ],
)
def test_binary_sensor_properties(
    mock_coordinator: MagicMock,
    sensor_type: str,
    *,
    is_connected: bool,
    expected: bool,
) -> None:
    """Test binary sensor properties for is_connected sensor type."""
    # Patch BINARY_SENSOR_TYPES to ensure sensor_type is valid
    with patch(
        "custom_components.sleepme_thermostat.binary_sensor.BINARY_SENSOR_TYPES",
        {sensor_type: "Test Sensor"},
    ):
        # Patch status for the device - the implementation only checks is_connected
        mock_coordinator.data["dev1"]["status"] = {"is_connected": is_connected}
        sensor = SleepmeBinarySensor(mock_coordinator, "dev1", sensor_type)
        # Name and unique_id
        assert sensor.name == "Bed 1 Test Sensor"
        assert sensor.unique_id == f"dev1_{sensor_type}"
        # is_on property - the implementation only checks is_connected regardless of
        # sensor_type
        assert sensor.is_on == expected


def test_binary_sensor_is_on_key_error(mock_coordinator: MagicMock) -> None:
    """Test binary sensor KeyError during initialization."""
    # The current implementation raises KeyError during __init__, not during is_on
    with pytest.raises(KeyError):
        SleepmeBinarySensor(mock_coordinator, "missing_dev", "is_connected")
