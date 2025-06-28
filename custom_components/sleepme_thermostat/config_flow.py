"""Sleep.me Config Flow for Home Assistant."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback

from .api import (
    SleepmeApiClient,
    SleepmeApiClientAuthenticationError,
    SleepmeApiClientError,
)
from .const import (
    CONF_API_KEY,
    DOMAIN,
)
from .data import SleepmeConfigEntry


class SleepmeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Sleep.me."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize."""
        self._errors = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            try:
                await validate_api_key(self.hass, user_input["api_key"])
                return self.async_create_entry(
                    title=user_input["api_key"], data=user_input
                )
            except SleepmeApiClientAuthenticationError:
                self._errors["base"] = "auth"
            except SleepmeApiClientError:
                self._errors["base"] = "unknown"

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
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SleepmeOptionsFlowHandler(config_entry)

    async def _show_config_form(
        self,
        user_input: dict[str, Any] | None,  # noqa: ARG002
    ) -> config_entries.ConfigFlowResult:
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("api_key"): str}),
            errors=self._errors,
        )


async def validate_api_key(hass: HomeAssistant, api_key: str) -> list[dict[str, Any]]:
    """Validate the API key by making a test call."""
    session = hass.helpers.aiohttp_client.async_get_clientsession()
    try:
        client = SleepmeApiClient(api_key, session)
        return await client.async_get_devices()
    except SleepmeApiClientError:
        return []


class SleepmeOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for Sleep.me."""

    def __init__(self, config_entry: SleepmeConfigEntry) -> None:
        """Initialize HACS options flow."""
        self._config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "api_key",
                        default=self.options.get("api_key"),
                    ): str,
                }
            ),
        )

    async def _update_options(self) -> config_entries.ConfigFlowResult:
        """Update config entry options."""
        return self.async_create_entry(title="Sleep.me", data=self.options)
