"""Tests for the SleepmeDataUpdateCoordinator module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.sleepme_thermostat.coordinator import (
    SleepmeDataUpdateCoordinator,
)


class DummyConfigEntry:
    """Dummy config entry."""


@pytest.mark.asyncio
async def test_async_set_device_mode_sets_control() -> None:
    """Test async_set_device_mode updates the device control data."""
    # Setup mock API client and config entry
    mock_api_client = AsyncMock()
    mock_api_client.async_set_device_mode = AsyncMock(
        return_value={"thermal_control_status": "active"}
    )
    mock_runtime_data = MagicMock()
    mock_runtime_data.client = mock_api_client
    mock_config_entry = MagicMock()
    mock_config_entry.runtime_data = mock_runtime_data

    # Setup coordinator with mock config entry and data
    mock_hass = MagicMock()
    coordinator = SleepmeDataUpdateCoordinator(
        mock_hass, mock_config_entry, name="test"
    )
    coordinator.config_entry = mock_config_entry
    coordinator.data = {"dev1": {"control": {}}}

    # Call the public method
    await coordinator.async_set_device_mode("dev1", "active")

    # Assert API client was called
    mock_api_client.async_set_device_mode.assert_awaited_once_with("dev1", "active")
    # Assert coordinator data was updated
    assert coordinator.data["dev1"]["control"] == {"thermal_control_status": "active"}
