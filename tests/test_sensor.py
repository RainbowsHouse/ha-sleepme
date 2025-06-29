"""Test sensor for Sleep.me Thermostat."""

import aiohttp
import pytest
from aioresponses import aioresponses
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sleepme_thermostat.const import (
    CONF_API_KEY,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_sensor(hass: HomeAssistant, aioresponses: aioresponses) -> None:
    """Test sensor."""
    aioresponses.get(
        "https://api.developer.sleep.me/v1/devices",
        headers={
            "Authorization": "Bearer 1234567890",
            "Content-Type": "application/json",
        },
        payload=[{"id": "abcd", "name": "A Bed", "attachments": ["CHILIPAD_PRO"]}],
    )
    aioresponses.get(
        "https://api.developer.sleep.me/v1/devices/abcd",
        headers={
            "Authorization": "Bearer 1234567890",
            "Content-Type": "application/json",
        },
        payload={
            "about": {
                "firmware_version": "5.39.2134",
                "ip_address": "70.190.108.13",
                "lan_address": "192.168.1.230",
                "mac_address": "b4:8a:0a:4f:90:54",
                "model": "DP999NA",
                "serial_number": "32404160372",
            },
            "control": {
                "brightness_level": 100,
                "display_temperature_unit": "f",
                "set_temperature_c": 21.5,
                "set_temperature_f": 71,
                "thermal_control_status": "standby",
                "time_zone": "America/Phoenix",
            },
            "status": {
                "is_connected": True,
                "is_water_low": False,
                "water_level": 100,
                "water_temperature_f": 74,
                "water_temperature_c": 23.5,
            },
        },
    )
    async with aiohttp.ClientSession():
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "id": "abcd",
                "name": "A Bed",
                CONF_API_KEY: "1234567890",
                CONF_UPDATE_INTERVAL: 10,
            },
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state_water_temperature_f = hass.states.get("sensor.a_bed_water_temperature_f")
        state_water_temperature_c = hass.states.get("sensor.a_bed_water_temperature_c")
        state_water_level = hass.states.get("sensor.a_bed_water_level")

        assert state_water_temperature_f
        assert state_water_temperature_f.state == "74"
        assert state_water_temperature_c
        assert state_water_temperature_c.state == "23.5"
        assert state_water_level
        assert state_water_level.state == "100"
