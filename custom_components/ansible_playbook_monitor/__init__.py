import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.dispatcher import (
    async_dispatcher_send,
    async_dispatcher_connect,
)
from homeassistant.components.webhook import async_register as webhook_async_register
from homeassistant.components.webhook import (
    async_unregister as webhook_async_unregister,
)
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ansible_playbook_monitor"
WEBHOOK_ID = "ansible_playbook_monitor_webhook"
DISPATCHER_SIGNAL = f"{DOMAIN}_update_signal"
PLATFORMS = ["sensor"]
STORAGE_KEY = "ansible_playbook_monitor"
STORAGE_VERSION = 1

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize persistent storage
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    hass.data[DOMAIN]["store"] = store

    # Load existing entities
    persisted_data = await store.async_load()
    if not persisted_data:
        persisted_data = {"entities": {}}
    hass.data[DOMAIN]["entities"] = persisted_data.get("entities", {})

    async def save_entities():
        """Persist entities to storage."""
        _LOGGER.debug("Saving entities: %s", hass.data[DOMAIN]["entities"])
        await store.async_save({"entities": hass.data[DOMAIN]["entities"]})

    hass.data[DOMAIN]["save_entities"] = save_entities

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
        attributes = data.get("attributes", {})

        if not playbook or not status:
            _LOGGER.warning("Invalid webhook data received: %s", data)
            return

        _LOGGER.debug(
            "Webhook received: playbook='%s', status='%s', attributes='%s'",
            playbook,
            status,
            attributes,
        )

        # Dispatch signal to update sensors
        async_dispatcher_send(hass, DISPATCHER_SIGNAL, playbook, status, attributes)

        # Update persistent data
        entities = hass.data[DOMAIN]["entities"]
        entities[playbook] = {"status": status, "attributes": attributes}
        await save_entities()

    # Register the webhook
    webhook_async_register(
        hass, DOMAIN, "Ansible Playbook Monitor", WEBHOOK_ID, handle_webhook
    )

    # Forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Connect the signal dispatcher in sensor setup
    def handle_signal(playbook, status, attributes):
        _LOGGER.debug(
            "Signal received: Updating playbook='%s', status='%s', attributes='%s'",
            playbook,
            status,
            attributes,
        )
        # Implement additional logic to handle the signal, e.g., updating states.

    async_dispatcher_connect(hass, DISPATCHER_SIGNAL, handle_signal)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook_async_unregister(hass, WEBHOOK_ID)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
