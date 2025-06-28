"""Utils."""

from .const import DOMAIN, UNIQUE_ID_POSTFIX


def get_device_id(name: str):
    """Returns a prefixed device ID."""
    return f"{DOMAIN}_{name}"


def add_unique_id_postfix(unique_id):
    """Add unique ID postfix"""
    return unique_id + UNIQUE_ID_POSTFIX


def remove_unique_id_postfix(unique_id):
    """Remove unique ID postfix"""
    return unique_id[0 : -len(UNIQUE_ID_POSTFIX)]
