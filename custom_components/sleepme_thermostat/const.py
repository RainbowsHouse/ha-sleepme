"""Constants for Sleep.me."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Base component constants
NAME = "Sleep.me"
VERSION = "0.0.1"
DOMAIN = "sleepme_thermostat"

ATTRIBUTION = "Data provided by https://sleep.me/"
ISSUE_URL = "https://github.com/rainbowshouse/ha-sleepme/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
CLIMATE = "climate"
PLATFORMS = [BINARY_SENSOR, SENSOR, CLIMATE]

UNIQUE_ID_POSTFIX = ".climate"
CONF_SLEEP_ME_DEVICE = "sleepme_state"

# Configuration and options
CONF_ENABLED = "enabled"
CONF_API_KEY = "api_key"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_SCAN_INTERVAL = 5

SENSOR_TYPES = {
    "water_temperature_f": "Water Temperature (F)",
    "water_temperature_c": "Water Temperature (C)",
    "water_level": "Water Level",
}

BINARY_SENSOR_TYPES = {"is_water_low": "Is Water Low", "is_connected": "Connected"}


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
