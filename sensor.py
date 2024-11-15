from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN, DISPATCHER_SIGNAL


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor entities dynamically from the integration."""

    async def handle_playbook_update(playbook, status):
        """Handle updates to playbook status."""
        entity_id = f"sensor.{playbook}_status"
        existing_entity = next(
            (
                entity
                for entity in hass.data[DOMAIN]["entities"]
                if entity.unique_id == entity_id
            ),
            None,
        )
        if existing_entity:
            existing_entity.update_status(status)
        else:
            new_entity = AnsiblePlaybookSensor(playbook, status)
            hass.data[DOMAIN]["entities"].append(new_entity)
            async_add_entities([new_entity])

    # Initialize a storage for entities if it doesn't exist
    hass.data.setdefault(DOMAIN, {"entities": []})

    # Connect the dispatcher signal to handle updates
    async_dispatcher_connect(hass, DISPATCHER_SIGNAL, handle_playbook_update)


class AnsiblePlaybookSensor(SensorEntity):
    """Sensor entity representing an Ansible playbook status."""

    def __init__(self, playbook, status):
        self._playbook = playbook
        self._status = status
        self._attr_name = f"{playbook} Playbook Status"
        self._attr_unique_id = f"sensor.{playbook}_status"

    @property
    def state(self):
        return self._status

    def update_status(self, status):
        """Update the status and notify Home Assistant."""
        self._status = status
        self.async_write_ha_state()
