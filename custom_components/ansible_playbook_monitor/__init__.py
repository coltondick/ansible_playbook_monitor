import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.components.webhook import async_register as webhook_async_register
from homeassistant.components.webhook import (
    async_unregister as webhook_async_unregister,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ansible_playbook_monitor"
WEBHOOK_ID = "ansible_playbook_monitor_webhook"
DISPATCHER_SIGNAL = f"{DOMAIN}_update_signal"
PLATFORMS = ["sensor"]

# Define a configuration schema to indicate this integration is config-entry only
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    api_key = entry.data.get(CONF_API_KEY)

    async def handle_webhook(hass, webhook_id, request):
        """Handle incoming webhook."""
        # Validate API key
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {api_key}":
            _LOGGER.warning("Unauthorized webhook access attempt")
            return None

        data = await request.json()
        playbook = data.get("playbook")
        status = data.get("status")

        if not playbook or not status:
            _LOGGER.warning("Invalid webhook data received.")
            return

        _LOGGER.info(f"Updating playbook {playbook} with status {status}")
        async_dispatcher_send(hass, DISPATCHER_SIGNAL, playbook, status)

    # Register the webhook
    webhook_async_register(
        hass, DOMAIN, "Ansible Playbook Monitor", WEBHOOK_ID, handle_webhook
    )

    # Forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook_async_unregister(hass, WEBHOOK_ID)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
