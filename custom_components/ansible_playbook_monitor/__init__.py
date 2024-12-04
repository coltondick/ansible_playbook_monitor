import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.storage import Store
from homeassistant.helpers.dispatcher import (
    async_dispatcher_send,
    async_dispatcher_connect,
)
from homeassistant.helpers.entity_registry import async_get
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.webhook import (
    async_register as webhook_async_register,
    async_unregister as webhook_async_unregister,
)
from aiohttp.web import Response
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ansible_playbook_monitor"
WEBHOOK_ID = "ansible_playbook_monitor_webhook"
DELETE_WEBHOOK_ID = f"{DOMAIN}_delete_entity"
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

    # Register RESTful API
    hass.http.register_view(AnsiblePlaybookAPI(hass))

    # Register the webhooks
    async def handle_webhook(hass, webhook_id, request):
        """Handle incoming webhook."""
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

        # Generate or retrieve the entity_id
        entity_id = f"sensor.ansible_playbook_{playbook}"
        entities = hass.data[DOMAIN]["entities"]
        entities[playbook] = {
            "entity_id": entity_id,
            "status": status,
            "attributes": attributes,
        }
        await hass.data[DOMAIN]["save_entities"]()

        # Dispatch signal to update sensors
        async_dispatcher_send(hass, DISPATCHER_SIGNAL, playbook, status, attributes)

    webhook_async_register(
        hass, DOMAIN, "Ansible Playbook Monitor", WEBHOOK_ID, handle_webhook
    )

    # Monitor entity registry for ID changes
    entity_registry = async_get(hass)

    @callback
    def handle_registry_updated(event):
        """Handle updates to the entity registry."""
        entity_id = event.data["entity_id"]
        old_entity_id = event.data.get("old_entity_id")

        if old_entity_id:
            # Update storage with the new entity ID
            entities = hass.data[DOMAIN]["entities"]
            playbook = next(
                (k for k, v in entities.items() if v["entity_id"] == old_entity_id),
                None,
            )
            if playbook:
                entities[playbook]["entity_id"] = entity_id
                _LOGGER.info(
                    f"Entity ID updated in storage: {old_entity_id} -> {entity_id}"
                )
                hass.async_create_task(hass.data[DOMAIN]["save_entities"]())

    hass.bus.async_listen("entity_registry_updated", handle_registry_updated)

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


class AnsiblePlaybookAPI(HomeAssistantView):
    """Handle RESTful API for Ansible Playbook Monitor."""

    url = "/api/ansible_playbook"
    name = "api:ansible_playbook"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    async def post(self, request):
        """Handle POST to create or update an entity."""
        data = await request.json()
        playbook = data.get("playbook")
        status = data.get("status")
        attributes = data.get("attributes", {})

        if not playbook or not status:
            return self.json_message("Invalid payload", 400)

        # Generate or retrieve the entity_id
        entity_id = f"sensor.ansible_playbook_{playbook}"
        entities = self.hass.data[DOMAIN]["entities"]
        entities[playbook] = {
            "entity_id": entity_id,
            "status": status,
            "attributes": attributes,
        }
        await self.hass.data[DOMAIN]["save_entities"]()

        # Update Home Assistant entity
        async_dispatcher_send(
            self.hass, DISPATCHER_SIGNAL, playbook, status, attributes
        )
        return self.json_message(f"Entity {entity_id} created/updated", 200)

    async def delete(self, request):
        """Handle DELETE to remove an entity."""
        data = await request.json()
        entity_id = data.get("entity_id")
        if not entity_id:
            _LOGGER.warning("DELETE request missing 'entity_id'")
            return self.json_message("Entity ID is required for deletion", 400)

        entities = self.hass.data[DOMAIN]["entities"]
        playbook = next(
            (k for k, v in entities.items() if v.get("entity_id") == entity_id), None
        )
        if not playbook:
            _LOGGER.warning(f"Entity ID {entity_id} not found in storage")
            return self.json_message("Entity not found", 404)

        # Remove from registry and persistent storage
        entity_registry = async_get(self.hass)
        if entity_registry.async_is_registered(entity_id):
            entity_registry.async_remove(entity_id)

        del entities[playbook]
        await self.hass.data[DOMAIN]["save_entities"]()
        return self.json_message(f"Entity {entity_id} deleted", 200)

    async def get(self, request):
        """Handle GET to retrieve entities."""
        entities = self.hass.data[DOMAIN]["entities"]
        return self.json(entities)
