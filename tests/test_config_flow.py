"""Test the Simple Integration config flow."""

from unittest.mock import patch

import aiohttp
from homeassistant import config_entries, setup
import pytest

from custom_components.sleepme_thermostat.const import CONF_API_KEY, DOMAIN


@pytest.mark.asyncio
async def test_form(hass, aioresponses):
    """Test we get the form."""
    aioresponses.get(
        "https://api.sleep.me/v1/devices",
        payload=[{"id": "1234567890", "name": "Sleep.me"}],
    )
    async with aiohttp.ClientSession() as session:
        await setup.async_setup_component(hass, "persistent_notification", {})
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"
        assert result["errors"] == {}

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

        assert result2["type"] == "form"
        # assert result2["title"] == "Sleep.me"
        # assert result2["data"] == {
        #     CONF_API_KEY: "1234567890",
        #     CONF_UPDATE_INTERVAL: 10,
        # }

        await hass.async_block_till_done()

        assert len(mock_setup.mock_calls) == 0
        assert len(mock_setup_entry.mock_calls) == 0
