"""Test the Simple Integration config flow."""

from unittest.mock import patch

import aiohttp
import pytest
from aioresponses import aioresponses
from homeassistant import config_entries, setup
from homeassistant.core import HomeAssistant

from custom_components.sleepme_thermostat.const import CONF_API_KEY, DOMAIN


@pytest.mark.asyncio
async def test_form(hass: HomeAssistant, aioresponses: aioresponses) -> None:
    """Test we get the form."""
    aioresponses.get(
        "https://api.sleep.me/v1/devices",
        payload=[{"id": "1234567890", "name": "Sleep.me"}],
    )
    async with aiohttp.ClientSession():
        await setup.async_setup_component(hass, "persistent_notification", {})
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result.get("type") == "form"
        assert result.get("errors") == {}

        with (
            patch(
                "custom_components.sleepme_thermostat.async_setup", return_value=True
            ) as mock_setup,
            patch(
                "custom_components.sleepme_thermostat.async_setup_entry",
                return_value=True,
            ) as mock_setup_entry,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: "1234567890"},
            )

        assert result2.get("type") == "form"

        await hass.async_block_till_done()

        assert len(mock_setup.mock_calls) == 0
        assert len(mock_setup_entry.mock_calls) == 0
