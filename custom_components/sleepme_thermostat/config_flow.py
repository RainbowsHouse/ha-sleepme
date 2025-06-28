"""Adds config flow for Sleep.me."""

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import SleepmeApiClient
from .api import SleepmeApiClientError
from .const import CONF_API_KEY
from .const import CONF_UPDATE_INTERVAL
from .const import DEFAULT_SCAN_INTERVAL
from .const import DOMAIN
from .const import LOGGER
from .const import PLATFORMS
from .data import SleepmeConfigEntry


class SleepmeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Sleep.me."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            try:
                devices = await validate_api_key(self.hass, user_input[CONF_API_KEY])
                LOGGER.info(f"Devices: {json.dumps(devices, indent=2)}")
                if len(devices) > 0:
                    await self.async_set_unique_id(user_input[CONF_API_KEY])
                    return self.async_create_entry(title="Sleep.me", data=user_input)
                else:
                    self._errors["base"] = "no_devices"
            except SleepmeApiClientError:
                self._errors["base"] = "auth"
            except Exception:
                self._errors["base"] = "unknown"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}

        if user_input:
            try:
                devices = await validate_api_key(self.hass, user_input[CONF_API_KEY])
                if len(devices) > 0:
                    await self.async_set_unique_id(user_input[CONF_API_KEY])
                    self._abort_if_unique_id_mismatch(reason="wrong_account")
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates={**user_input, "devices": devices},
                    )
                else:
                    errors["base"] = "no_devices"
            except SleepmeApiClientError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: SleepmeConfigEntry,
    ):
        return SleepmeOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): int,
                }
            ),
            errors=self._errors,
        )


async def validate_api_key(hass: HomeAssistant, api_key: str) -> list[dict]:
    """Validate the API key."""
    try:
        session = async_create_clientsession(hass)
        client = SleepmeApiClient(api_key, session)
        return await client.async_get_devices()
    except Exception:  # pylint: disable=broad-except
        pass
    return []


class SleepmeOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for Sleep.me."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self._config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(title="Sleep.me", data=self.options)
