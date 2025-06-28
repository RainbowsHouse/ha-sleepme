"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import SleepmeApiClient
    from .coordinator import SleepmeDataUpdateCoordinator


type SleepmeConfigEntry = ConfigEntry[SleepmeData]


@dataclass
class SleepmeData:
    """Data for the Sleep.me integration."""

    client: SleepmeApiClient
    coordinator: SleepmeDataUpdateCoordinator
    integration: Integration
