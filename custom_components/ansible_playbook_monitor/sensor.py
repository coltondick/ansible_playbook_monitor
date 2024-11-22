from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN, DISPATCHER_SIGNAL
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor entities dynamically from the integration."""

    async def handle_playbook_update(playbook, status, attributes=None):
        """Handle updates to playbook status."""
        _LOGGER.debug(
            "Processing update: playbook='%s', status='%s', attributes='%s'",
            playbook,
            status,
            attributes,
        )
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
            existing_entity.update_status(status, attributes)
        else:
            new_entity = AnsiblePlaybookSensor(playbook, status, attributes)
            hass.data[DOMAIN]["entities"].append(new_entity)
            async_add_entities([new_entity])

    # Initialize a storage for entities if it doesn't exist
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {"entities": []}

    # Listen for dispatcher signals
    async_dispatcher_connect(hass, DISPATCHER_SIGNAL, handle_playbook_update)


class AnsiblePlaybookSensor(SensorEntity):
    """Sensor representing an Ansible playbook's status."""

    def __init__(self, playbook, status, attributes=None):
        """Initialize the sensor."""
        self._playbook = playbook
        self._status = status
        self._attributes = attributes or {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._playbook} Status"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"sensor.{self._playbook}_status"

    @property
    def state(self):
        """Return the current state of the sensor."""
        return self._status

    @property
    def extra_state_attributes(self):
        """Return the attributes of the sensor."""
        return self._attributes

    def update_status(self, status, attributes=None):
        """Update the sensor's status and attributes."""
        self._status = status
        if attributes:
            self._attributes.update(attributes)
        _LOGGER.debug(
            "Updated sensor '%s': status='%s', attributes='%s'",
            self._playbook,
            self._status,
            self._attributes,
        )
        self.async_write_ha_state()
